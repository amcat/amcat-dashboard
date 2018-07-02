import json
from functools import wraps
from uuid import uuid4

from django.db import transaction
from django.template.response import TemplateResponse
from django.views.decorators.http import condition, require_http_methods
from requests import HTTPError

from dashboard.models.query import QueryCache
from dashboard.util.shortcuts import redirect_referrer, safe_referrer

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from django.core.urlresolvers import reverse
from django.conf import settings

from django.http import HttpResponse, Http404, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView, UpdateView

from dashboard.models import Query, Page, HighchartsTheme
from dashboard.util.api import start_task, get_session

from dashboard.models.user import EPOCH

class MenuViewMixin(object):
    pass

class BaseDashboardView(TemplateView):
    """Adds basic context to a view, for menu rendering."""
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        pages = Page.objects.filter(system=self.request.user.system).only("id", "name", "icon")
        return dict(super(BaseDashboardView, self).get_context_data(**kwargs), pages=pages)


class DashboardPageView(BaseDashboardView):
    def get_context_data(self, **kwargs):
        page = Page.objects.only("name", "icon").get(id=self.kwargs["page_id"])
        system = page.system

        # this is set as a JS global
        system_info = json.dumps({
            "id": system.id,
            "hostname": system.hostname,
            "project_id": system.project_id,
            "project_name": system.project_name
        })

        rows = page.get_cells(select_related=("row", "query"))
        themes = HighchartsTheme.objects.filter(cells__row__in=rows).distinct()
        return dict(super(DashboardPageView, self).get_context_data(**kwargs),
                    page=page, rows=rows, themes=themes, system_info=system_info)


# HTTP GET *must* be nullipotent: browsers might poll GET urls for preview or bookmark purposes.
@require_http_methods(['POST'])
def clear_cache(request, query_id):
    with transaction.atomic():
        query = Query.objects.select_for_update().get(id=query_id)
        query.clear_cache()
        query.update()
        query.save()

    try:
        start_task(get_session(query.system), query)
    except HTTPError as e:
        r = e.response # type HTTPResponse
        if r.status_code == 400:
            try:
                data = r.json()
            except:
                context = {}
            else:
                context = {
                    "error_text": "Query '{}' is invalid.".format(query.amcat_name),
                    "errors": data,
                    "back_href": safe_referrer(request)
                }
            return TemplateResponse(request, 'dashboard/query_error.html', status=400, context=context)
        raise

    return redirect_referrer(request, same_origin=True)


def get_saved_query(request, query_id, page_id):
    query = Query.objects.get(id=query_id)
    return HttpResponse(content_type="application/json", content=json.dumps({
        "id": query.id,
        "amcat_project_id": query.amcat_project_id,
        "amcat_query_id": query.amcat_query_id,
        "amcat_name": query.amcat_name,
        "amcat_parameters": query.get_parameters(),
        "amcat_options": query.get_options(),
        "amcat_url": query.amcat_url,
        "clear_cache_url": reverse('dashboard:clear-cache', args=[query_id]),
        "script": query.get_script(),
        "output_type": query.get_output_type(),
        "articleset_ids": query.get_articleset_ids(),
        "result_url": reverse('dashboard:get-saved-query-result', args=[page_id, query.id])
    }))


def query_last_modified(request, query_id, page_id):
    q = getattr(request, 'dashboard__query', None)
    if q is None:
        return None
    return q.cache_timestamp


def query_tag(request, query_id, page_id):
    try:
        q = QueryCache.objects.only('cache_timestamp').get(query_id=query_id, page_id=page_id)
        setattr(request, 'dashboard__query', q)
        return q.get_query_tag()
    except QueryCache.DoesNotExist:
        return None


def no_cache(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        response = view(*args, **kwargs)
        response.setdefault('Cache-Control', 'must-revalidate, post-check=0, pre-check=0')
        return response
    return wrapper


@no_cache
@condition(etag_func=query_tag, last_modified_func=query_last_modified)
def get_saved_query_result(request, query_id, page_id):
    """
    Returns the results of a saved query either from cache or from AmCAT server. This
    code is not thread-safe.
    """

    try:
        defaults = dict(query_id=query_id, page_id=page_id)
        cache, created = QueryCache.objects.get_or_create(defaults=defaults, **defaults)
    except QueryCache.DoesNotExist:
        raise Http404("No such object")

    # If we've still got one in cache, use that one
    if cache.is_valid():
        return HttpResponse(cache.cache, content_type=cache.cache_mimetype)

    # We need to fetch it from an amcat instance
    if not cache.is_valid():
        # Nothing in cache, start querying.
        # using a transaction to prevent multiple updates for the same query.
        with transaction.atomic():
            mut_query = QueryCache.objects.select_for_update().get(pk=cache.pk)
            # We weren't in a transaction before. Better check again
            if not cache.is_valid():
                mut_query.clear_cache()
                mut_query.refresh_cache()
                mut_query.save()
                cache = mut_query

            else:
                # Another request already initiated a refresh, tell the client to try again later..
                r = JsonResponse({"status": "pending"})
                r['Etag'] = ""

    # Return cached result
    return HttpResponse(cache.cache, content_type=cache.cache_mimetype)


def empty(request):
    return render(request, "dashboard/empty.html", locals())


def index(request):
    if not Page.objects.filter(system=request.user.system, visible=True).exists():
        return redirect(reverse("dashboard:empty"))

    first_page = Page.objects.filter(system=request.user.system).only("id").first()
    url_kwargs = {"page_id": first_page.id}
    return redirect(reverse("dashboard:view-page", kwargs=url_kwargs))


def queries(request, system_id):
    cron_secret = settings.CRON_SECRET
    server_port = request.META["SERVER_PORT"]
    epoch = EPOCH
    all_queries = Query.objects.filter(system__id=system_id).order_by("amcat_query_id").defer("cache", "amcat_parameters")
    return render(request, "dashboard/queries.html", locals())

import json
from functools import wraps

from django.db import transaction
from django.views.decorators.http import condition, require_http_methods

from dashboard.util.shortcuts import redirect_referrer

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from django.core.urlresolvers import reverse
from django.conf import settings

from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

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

    start_task(get_session(query.system), query)

    return redirect_referrer(request, same_origin=True)


def get_saved_query(request, query_id):
    query = Query.objects.get(id=query_id)
    return HttpResponse(content_type="application/json", content=json.dumps({
        "id": query.id,
        "amcat_project_id": query.amcat_project_id,
        "amcat_query_id": query.amcat_query_id,
        "amcat_name": query.amcat_name,
        "amcat_parameters": query.get_parameters(),
        "amcat_url": query.amcat_url,
        "clear_cache_url": reverse('dashboard:clear-cache', args=[query_id]),
        "script": query.get_script(),
        "output_type": query.get_output_type(),
        "articleset_ids": query.get_articleset_ids(),
        "result_url": reverse('dashboard:get-saved-query-result', args=[query.id])
    }))


def query_last_modified(request, query_id):
    return request.dashboard__query.cache_timestamp


def query_uuid(request, query_id):
    q = Query.objects.only("cache_timestamp", "cache_uuid").get(pk=query_id)
    setattr(request, 'dashboard__query', q)
    return q.cache_uuid


def no_cache(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        response = view(*args, **kwargs)
        response.setdefault('Cache-Control', 'no-cache')
        return response
    return wrapper


@no_cache
@condition(etag_func=query_uuid, last_modified_func=query_last_modified)
def get_saved_query_result(request, query_id):
    """
    Returns the results of a saved query either from cache or from AmCAT server. This
    code is not thread-safe.
    """
    try:
        query = Query.objects.get(id=query_id)
    except Query.DoesNotExist:
        raise Http404("No such object")

    # If we've still got one in cache, use that one
    if query.cache is not None:
        return HttpResponse(query.cache, content_type=query.cache_mimetype)

    # We need to fetch it from an amcat instance
    if query.cache_uuid is None:
        # Nothing in cache, start querying.
        # using a transaction to prevent multiple updates for the same query.
        with transaction.atomic():
            mut_query = Query.objects.select_for_update().get(pk=query.pk)
            # We weren't in a transaction before. Better check again
            if mut_query.cache_uuid is None:
                mut_query.refresh_cache()
                mut_query.save()
                query = mut_query

            else:
                # Another request already initiated a refresh, tell the client to try again later..
                return JsonResponse({"status": "pending"})

    # Return cached result
    return HttpResponse(query.cache, content_type=query.cache_mimetype)


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

import datetime
import json

from django.core.cache import caches
from django.db import transaction
from django.db.models.expressions import RawSQL
from django.template.response import TemplateResponse
from django.views.decorators.gzip import gzip_page
from django.views.decorators.http import require_http_methods
from requests import HTTPError

from dashboard.models.query import QueryCache
from dashboard.util.shortcuts import redirect_referrer, safe_referrer

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
        hide_menu = self.request.user.system.hide_menu and not self.request.user.is_superuser
        return dict(super(BaseDashboardView, self).get_context_data(**kwargs), pages=pages, hide_menu=hide_menu)


class DashboardPageView(BaseDashboardView):
    query_param = 'q'

    def get_context_data(self, **kwargs):
        page = Page.objects.only("name", "icon").get(id=self.kwargs["page_id"])
        system = page.system
        showintro = self.request.session.get("showintro", True)
        self.request.session["showintro"] = False
        # this is set as a JS global
        system_info = json.dumps({
            "id": system.id,
            "hostname": system.hostname,
            "project_id": system.project_id,
            "project_name": system.project_name
        })
        query = self.request.GET.get(self.query_param)

        rows = page.get_cells(select_related=("query",))
        themes = HighchartsTheme.objects.filter(cells__row__in=rows).distinct()
        return dict(super(DashboardPageView, self).get_context_data(**kwargs),
                    page=page, rows=rows, themes=themes, system_info=system_info, query=query, showintro=showintro)


# HTTP GET *must* be nullipotent: browsers might poll GET urls for preview or bookmark purposes.
@require_http_methods(['POST'])
def clear_cache(request, query_id):
    with transaction.atomic():
        query = Query.objects.select_for_update().get(id=query_id)
        query.clear_cache()
        query.update()
        query.save()

    try:
        if request.POST.get('refresh', False):
            for cache in query.querycache_set.all():
                with transaction.atomic():
                    cache = QueryCache.objects.select_for_update().get(pk=cache.id)
                    cache.refresh_cache()
        else:
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
                    "back_href": safe_referrer(request),
                    "action_href": query.amcat_url,
                    "action_text": "Edit on AmCAT"
                }
            return TemplateResponse(request, 'dashboard/query_error.html', status=400, context=context)
        raise

    return redirect_referrer(request, same_origin=True)


@gzip_page
def download_query(request, query_id, page_id):
    try:
        defaults = dict(query_id=query_id, page_id=page_id)
        cache, created = QueryCache.objects.get_or_create(defaults=defaults, **defaults)
    except QueryCache.DoesNotExist:
        raise Http404("No such object")

    uuid = cache.start_task(extra_options={"output_type": "text/csv"})
    cache.uuid = uuid
    cache.save()

    content, content_type = cache.poll(uuid)

    return HttpResponse(content_type=content_type, content=content)

@gzip_page
def download_query_results(request, *, page_id, query_id, uuid):
    try:
        query = Query.objects.get(pk=query_id)
    except Query.DoesNotExist:
        raise Http404("No such object")

    response = get_session(query.system).get_task_result(uuid)
    content = response.content.decode('utf-8')
    content_type = response.headers.get("Content-Type")
    return HttpResponse(content=content, content_type=content_type)

@gzip_page
def poll_query_by_uuid(request, *, query_id, page_id, query_uuid):
    try:
        cache = QueryCache.objects.get(query_id=query_id, page_id=page_id)
    except QueryCache.DoesNotExist:
        raise Http404("No such object")

    status, result = cache.poll_once(query_uuid)
    result["result_url"] = reverse("dashboard:download-query-results", args=(page_id, query_id, query_uuid))
    return JsonResponse(result)

@gzip_page
def init_download_query(request, query_id, page_id):
    try:
        defaults = dict(query_id=query_id, page_id=page_id)
        cache, created = QueryCache.objects.get_or_create(defaults=defaults, **defaults)
    except QueryCache.DoesNotExist:
        raise Http404("No such object")

    uuid = cache.start_task(extra_options={"output_type": "text/csv"})
    return JsonResponse({"poll_uri": reverse('dashboard:poll-query-by-uuid', args=(page_id, query_id, uuid))})



@gzip_page
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
        "init_download_url": reverse('dashboard:init-download-query', args=[page_id, query_id]),
        "download_url": reverse('dashboard:download-query', args=[page_id, query_id]),
        "is_downloadable": query.get_script().endswith("aggregation"),
        "script": query.get_script(),
        "output_type": query.get_output_type(),
        "articleset_ids": query.get_articleset_ids(),
        "result_url": reverse('dashboard:get-saved-query-result', args=[page_id, query.id])
    }))



@gzip_page
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

    query_val = request.GET.get(DashboardPageView.query_param)

    if query_val and query_val.strip():
        return get_filtered_query_result(request, cache)

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

def get_filtered_query_result(request, query_cache: QueryCache):
    query_override = request.GET[DashboardPageView.query_param]

    cache_key = query_cache.get_query_tag(query_override=query_override)
    cached = caches['query'].get(cache_key)

    if not cached or cached['timestamp'].replace(tzinfo=datetime.timezone.utc) < query_cache.cache_timestamp.astimezone():
        uuid = query_cache.start_task(query_override=query_override)
        content, content_type = query_cache.poll(uuid, save_result=False)
        caches['query'].set(cache_key, {
            "content": content,
            "content_type": content_type,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc)
        })
        return HttpResponse(content, content_type=content_type)
    print('From cache: {}'.format(request.get_raw_uri()))
    return HttpResponse(cached['content'], content_type=cached['content_type'])


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
    epoch = EPOCH + datetime.timedelta(minutes=1)

    # Order by -has_cache, cache_timestamp to sort in order of [older cache, newer cache, no cache]
    caches = QueryCache.objects.filter(query__system_id=system_id) \
        .annotate(has_cache=RawSQL('cache_timestamp > %s', (epoch.isoformat(),))) \
        .order_by('query_id', '-has_cache', 'cache_timestamp') \
        .distinct('query_id').values('pk')

    caches = QueryCache.objects.filter(pk__in=caches) \
        .annotate(has_cache=RawSQL('cache_timestamp > %s', (epoch.isoformat(),)))\
        .order_by('query__amcat_query_id')

    uncached = Query.objects.filter(system_id=system_id,querycache=None).order_by('amcat_query_id')


    return render(request, "dashboard/queries.html", locals())

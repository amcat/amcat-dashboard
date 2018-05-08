import datetime
import json
from functools import wraps

from django.views.decorators.http import etag, condition

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from django.core.urlresolvers import reverse

from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from dashboard.models import Query, Page, System
from dashboard.util.api import poll, start_task, get_session

class MenuViewMixin(object):
    pass

class BaseDashboardView(TemplateView):
    """Adds basic context to a view, for menu rendering."""
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        pages = Page.objects.all().only("id", "name", "icon")
        return dict(super(BaseDashboardView, self).get_context_data(**kwargs), pages=pages)

class DashboardPageView(BaseDashboardView):
    def get_context_data(self, **kwargs):
        page = Page.objects.only("name", "icon").get(id=self.kwargs["page_id"])
        rows = page.get_cells(select_related=("row", "query"))
        return dict(super(DashboardPageView, self).get_context_data(**kwargs), page=page, rows=rows)

def clear_cache(request, query_id):
    query = Query.objects.get(id=query_id)
    query.clear_cache()
    query.update()
    query.save()

    start_task(get_session(query.system), query)

    return redirect(reverse("dashboard:index"))

def get_saved_query(request, query_id):
    query = Query.objects.get(id=query_id)
    return HttpResponse(content_type="application/json", content=json.dumps({
        "amcat_project_id": query.amcat_project_id,
        "amcat_query_id": query.amcat_query_id,
        "amcat_name": query.amcat_name,
        "amcat_parameters": query.get_parameters(),
        "script": query.get_script(),
        "output_type": query.get_output_type(),
        "articleset_ids": query.get_articleset_ids()
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
    s = get_session(query.system)

    if query.cache_uuid is None:
        # Start job
        s.headers["Content-Type"] = "application/x-www-form-urlencoded"
        url = "{host}/api/v4/query/{script}?format=json&project={project}&sets={sets}&jobs={jobs}".format(**{
            "sets": ",".join(map(str, query.get_articleset_ids())),
            "jobs": ",".join(map(str, query.get_codingjob_ids())),
            "project": query.amcat_project_id,
            "query": query.amcat_query_id,
            "script": query.get_script(),
            "host": System.load().hostname
        })

        response = s.post(url, data=urlencode(query.get_parameters(), True))
        uuid = json.loads(response.content.decode("utf-8"))["uuid"]
        query.cache_uuid = uuid
        query.save()

    # We need to wait for the result..
    result = poll(s, query.cache_uuid)

    # Cache results
    query.cache = result.content.decode('utf-8')
    query.cache_timestamp = datetime.datetime.now()
    query.cache_mimetype = result.headers.get("Content-Type")
    query.save()

    # Return cached result
    return HttpResponse(query.cache, content_type=query.cache_mimetype)


def empty(request):
    return render(request, "dashboard/empty.html", locals())

def index(request):
    if not Page.objects.filter(visible=True).exists():
        return redirect(reverse("dashboard:empty"))

    first_page = Page.objects.all().only("id")[0]
    url_kwargs = {"page_id": first_page.id}
    return redirect(reverse("dashboard:view-page", kwargs=url_kwargs))


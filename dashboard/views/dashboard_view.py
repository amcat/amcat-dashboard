import datetime
import json
from urllib.parse import urlencode

from django.core.urlresolvers import reverse

from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect

from dashboard.models import Query
from dashboard.util.api import poll, start_task, PREVIEW_URL, get_session


def clear_cache(request, query_id):
    query = Query.objects.get(id=query_id)
    query.clear_cache()
    query.update()
    query.save()

    start_task(get_session(), query)

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

    # We need to fetch it from preview.amcat.nl
    s = get_session()

    if query.cache_uuid is None:
        # Start job
        s.headers["Content-Type"] = "application/x-www-form-urlencoded"
        url = PREVIEW_URL + "query/{script}?format=json&project={project}&sets={sets}".format(**{
            "sets": ",".join(map(str, query.get_articleset_ids())),
            "project": query.amcat_project_id,
            "query": query.amcat_query_id,
            "script": query.get_script()
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


def index(request):
    q1 = Query.objects.get(id=1)
    q2 = Query.objects.get(id=2)
    q3 = Query.objects.get(id=3)
    q4 = Query.objects.get(id=4)
    q5 = Query.objects.get(id=5)

    return render(request, "dashboard/dashboard.html", locals())


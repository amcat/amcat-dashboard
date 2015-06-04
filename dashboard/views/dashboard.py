import datetime
import json
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.generic import FormView
import requests

from dashboard.models import User, Query

PREVIEW_URL = "http://preview.amcat.nl/api/v4/"
TASK_URL = PREVIEW_URL + "task?uuid={uuid}&format=json"
TASKRESULT_URL = PREVIEW_URL + "taskresult/{uuid}?format=json"

class STATUS:
    INPROGRESS = "INPROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILURE"
    PENDING = "PENDING"

def poll(session, uuid, timeout=0.2, max_timeout=2):
    response = session.get(TASK_URL.format(uuid=uuid))
    task = json.loads(response.content.decode("utf-8"))
    status = task["results"][0]["status"]

    if status in (STATUS.INPROGRESS, STATUS.PENDING):
        return poll(session, uuid, timeout=min(timeout * 2, max_timeout))
    elif status == STATUS.FAILED:
        raise ValueError("Task {!r} failed.".format(uuid))
    elif status == STATUS.SUCCESS:
        return session.get(TASKRESULT_URL.format(uuid=uuid))
    else:
        raise ValueError("Unknown status value {!r} returned.".format(status))

def start_task(session, query):
    if query.cache_uuid is not None:
        return query.cache_uuid

    # Start job
    session.headers["Content-Type"] = "application/x-www-form-urlencoded"
    url = PREVIEW_URL + "query/{script}?format=json&project={project}&sets={sets}".format(**{
        "sets": ",".join(map(str, query.get_articleset_ids())),
        "project": query.amcat_project_id,
        "query": query.amcat_query_id,
        "script": query.get_script()
    })

    response = session.post(url, data=urlencode(query.get_parameters(), True))
    uuid = json.loads(response.content.decode("utf-8"))["uuid"]
    query.cache_uuid = uuid
    query.save()

    return uuid

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

def get_session():
    session = requests.Session()
    session.cookies.set("sessionid", settings.SESSION_ID, domain="preview.amcat.nl")
    session.get("http://preview.amcat.nl")
    session.headers["X-CSRFTOKEN"] = session.cookies.get("csrftoken")
    return session


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
    clustermap = Query.objects.get(id=1)
    geenstijl = Query.objects.get(id=2)
    dagbladen = Query.objects.get(id=3)
    return render(request, "dashboard/dashboard.html", locals())

class UserForm(forms.ModelForm):
    amcat_token = forms.CharField(required=False)
    amcat_username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    def clean(self):
        data = super().clean()

        url = "http://preview.amcat.nl/api/v4/get_token"
        response = requests.post(url, data={
            'username': data["amcat_username"],
            'password': data["password"]
        })

        if (response.status_code != 200):
            raise ValidationError("AmCAT replied with status code {}".format(response.status_code))

        data["amcat_token"] = json.loads(response.content.decode("utf-8"))["token"]

        return data

    class Meta:
        model = User
        fields = ("amcat_token", "amcat_username")

class AmCATSettingsView(FormView):
    form_class = UserForm
    template_name = "dashboard/amcat_settings.html"

    def get_success_url(self):
        return reverse("dashboard:amcat-settings")

    def get_form_kwargs(self):
        return dict(super().get_form_kwargs(), instance=self.request.user)

    def form_valid(self, form):
        resp = super().form_valid(form)
        form.save()
        return resp

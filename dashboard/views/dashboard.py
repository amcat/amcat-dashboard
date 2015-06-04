import json
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.views.generic import FormView
import requests

from dashboard.models import User, Query

PREVIEW_URL = "http://preview.amcat.nl/api/v4/query/"


def index(request):
    s = requests.Session()

    sessionid = settings.SESSION_ID

    # Login using session id provided via environment variables
    s.cookies.set("sessionid", settings.SESSION_ID, domain="preview.amcat.nl")

    # Get CSRF token
    s.get("http://preview.amcat.nl")
    s.headers["X-CSRFTOKEN"] = s.cookies.get("csrftoken")
    csrftoken = s.cookies.get("csrftoken")

    query, = Query.objects.all()

    url = PREVIEW_URL + "{script}?format=json&project={project}&sets={sets}".format(**{
        "sets": ",".join(map(str, query.get_articleset_ids())),
        "project": query.amcat_project_id,
        "query": query.amcat_query_id,
        "script": query.get_script()
    })

    s.headers["Content-Type"] = "application/x-www-form-urlencoded"
    response = s.post(url, data=urlencode(query.get_parameters(), True))
    uuid = json.loads(response.content.decode("utf-8"))["uuid"]

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

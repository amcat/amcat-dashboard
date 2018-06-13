import json

from amcatclient import APIError
from django import forms
from django.contrib.postgres.forms import JSONField, ValidationError
from django.http import HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponse, JsonResponse
from django.views import View
from django.views.generic import FormView

from dashboard.models import System
from dashboard.util.api import search
from dashboard.views.settings import SystemMixin


class SearchView(SystemMixin, View):

    @property
    def echo(self):
        opts = self.request.GET.get('datatables_options', self.request.POST.get('datatables_options'))
        if opts is not None:
            try:
                return json.loads(opts).get('sEcho')
            except json.JSONDecodeError:
                return None

    def get_search(self, method='get'):
        filters = dict(self.request.GET, **self.request.POST)
        system = self.system
        return search(system, method_=method, **filters)

    def options(self, request, *args, **kwargs):
        return self.handle("options")

    def get(self, request, *args, **kwargs):
        return self.handle("get")

    def handle(self, method):
        try:
            search_result = self.get_search(method=method)
        except APIError as e:

            if e.http_status == 400:
                status = 400  # invalid request
                message = "Invalid request"
            else:
                status = 503  # Service Unavailable
                message = "An error occurred while retrieving the resource."

            return JsonResponse({
                "message": message,
                "responseStatus": e.http_status,
                "response": str(e.response)
            }, status=status)

        echo = self.echo
        if echo is not None:
            search_result.update(echo=echo)
        return JsonResponse(search_result)

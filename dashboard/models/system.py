from __future__ import absolute_import

import logging
from collections import defaultdict

from amcatclient import AmcatAPI
from amcatclient.amcatclient import Unauthorized, APIError
from django.db import models
from django.utils.translation import gettext as _

from dashboard.models import Query


class System(models.Model):
    hostname = models.TextField(default="")
    project_id = models.PositiveIntegerField(help_text=_("AmCAT project this dashboard is linked to"), null=True)
    project_name = models.TextField(null=True)
    amcat_token = models.TextField(null=True)

    def synchronise_queries(self):
        url = "projects/{project}/querys/".format(project=self.project_id)

        for api_query in self.get_api().get_pages(url):
            amcat_query_id = api_query["id"]

            try:
                query = Query.objects.get(amcat_query_id=amcat_query_id)
            except Query.DoesNotExist:
                query = Query(amcat_query_id=amcat_query_id)

            query.system = self
            query.amcat_name = api_query["name"]
            query.amcat_parameters = api_query["parameters"]
            query.save()

    def save(self, *args, **kwargs):
        if self.project_name is None:
            try:
                api = self.get_api()
                response = api.request('projects/{}/'.format(self.project_id))
                self.project_name = response['name']
            except Exception as e:
                logging.error(e)
                pass

        super(System, self).save(*args, **kwargs)

    def get_global_filters(self):
        filterdict = defaultdict(list)
        for filter in self.filter_set.all():
            filterdict[filter.field].append(filter.value)
        return filterdict


    def set_token(self, username, password):
        self.amcat_token = self.get_api(username, password).token

    def get_api(self, username=None, password=None):
        """
        Get amcatclient API object. If username and password is given, authenticate with
        those credentials, else use System.token.

        @return: AmcatAPI
        """
        if username and password:
            return AmcatAPI(host=self.hostname, user=username, password=password)
        assert self.amcat_token, "No username and password supplied, but no token was set too."
        return AmcatAPI(host=self.hostname, token=self.amcat_token)

    def ping(self):
        """
        Get a quick status update from the server. Returns the authorized user if successful. If not,
        it returns None and an error message.

        @return: a tuple (user | None, error | None)
        """
        try:
            return self.get_api().request('users/me/'), None
        except Unauthorized:
            return None, "401: Unauthorized (did your token expire?)"
        except APIError as api_err:
            err = api_err
            if api_err.http_status == 404:
                try:
                    response = self.get_api().request('')
                    return response, None
                except APIError as api_err:
                    err = api_err

            return None, "%(status_code)s: %(description)s" % {
                "status_code": err.http_status,
                "description": err.description if err.description else err.response
            }
        except Exception as e:
            logging.warning("Unexpected API error: {}".format(e))
            return None, e

    @classmethod
    def load(cls):
        return cls.objects.get()


    def __str__(self):
        project_name = "{{}}: {}".format(self.project_name) if self.project_name is not None else "Project {}"
        project_name = project_name.format(self.project_id)
        return "{}, {}".format(project_name, self.hostname)
    
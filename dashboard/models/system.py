from __future__ import absolute_import

from django.conf import settings
from django.db import models

from amcatclient import AmcatAPI
from dashboard.models import Query


class System(models.Model):
    hostname = models.TextField(default="http://preview.amcat.nl")
    project_id = models.PositiveIntegerField(help_text="AmCAT project this dashboard is linked to", null=True)
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

            query.amcat_name = api_query["name"]
            query.amcat_parameters = api_query["parameters"]
            query.amcat_project_id = api_query["project"]
            query.save()

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(System, self).save(*args, **kwargs)

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

    @classmethod
    def load(cls):
        return cls.objects.get()



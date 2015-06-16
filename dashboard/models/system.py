from __future__ import absolute_import

from django.conf import settings
from django.db import models

from amcatclient import AmcatAPI
from dashboard.models import Query


class System(models.Model):
    api_user = models.ForeignKey(settings.AUTH_USER_MODEL, help_text="User on whose behalf API calls are made to AmCAT")
    hostname = models.TextField(default="http://preview.amcat.nl")
    project_id = models.PositiveIntegerField(help_text="AmCAT project this dashboard is linked to", null=True)
    project_name = models.TextField(null=True)

    def synchronise_queries(self):
        api = self.api_user.get_api(self.hostname)
        url = "projects/{project}/querys/".format(project=self.project_id)

        for api_query in api.get_pages(url):
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

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()

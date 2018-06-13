from __future__ import absolute_import

import json

from django.db import models
from dashboard.models.user import EPOCH


class Query(models.Model):
    system = models.ForeignKey("dashboard.System", on_delete=models.CASCADE)

    amcat_query_id = models.IntegerField(db_index=True, unique=True)

    amcat_name = models.TextField()
    amcat_parameters = models.TextField()

    # To prevent bombarding the AmCAT servers with request, we cache results. These
    # caches might be refreshed by a cronjob or manually
    cache = models.TextField(null=True)
    cache_timestamp = models.DateTimeField(default=EPOCH)
    cache_mimetype = models.TextField(null=True)
    cache_uuid = models.TextField(null=True)

    @property
    def amcat_project_id(self):
        return self.system.project_id

    @property
    def amcat_url(self):
        return "{hostname}/projects/{project_id}/query/{query_id}".format(
            hostname=self.system.hostname,
            project_id=self.system.project_id,
            query_id=self.amcat_query_id
        )

    def get_parameters(self):
        parameters = json.loads(self.amcat_parameters)
        try:
            filters = json.loads(parameters['filters'])
        except (KeyError, json.JSONDecodeError):
            filters = {}
        filters.update(self.system.get_global_filters())
        return dict(parameters, filters=json.dumps(filters))


    def get_articleset_ids(self):
        return list(map(int, self.get_parameters()["articlesets"]))

    def get_codingjob_ids(self):
        return list(map(int, self.get_parameters().get("codingjobs", [])))

    def get_script(self):
        return self.get_parameters()["script"]

    def get_output_type(self):
        return self.get_parameters()["output_type"]

    def clear_cache(self):
        self.cache = None
        self.cache_timestamp = EPOCH
        self.cache_mimetype = None
        self.cache_uuid = None

    def update(self):
        from dashboard.util.api import get_session  # don't move this, will result in an import cycle.

        url = "{host}/api/v4/projects/{project}/querys/{query}/?format=json"
        url = url.format(
            project=self.system.project_id,
            query=self.amcat_query_id,
            host=self.system.hostname
        )

        data = json.loads(get_session(self.system).get(url).content.decode('utf-8'))
        self.amcat_name = data["name"]
        self.amcat_parameters = data["parameters"]



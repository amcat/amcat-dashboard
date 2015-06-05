import json
from django.conf import settings
from django.db import models
import requests
from dashboard.models.user import EPOCH


class Query(models.Model):
    amcat_query_id = models.IntegerField(db_index=True, unique=True)
    amcat_project_id = models.IntegerField(db_index=True)

    amcat_name = models.TextField()
    amcat_parameters = models.TextField()

    # To prevent bombarding the AmCAT servers with request, we cache results. These
    # caches might be refreshed by a cronjob or manually
    cache = models.TextField(null=True)
    cache_timestamp = models.DateTimeField(default=EPOCH)
    cache_mimetype = models.TextField(null=True)
    cache_uuid = models.TextField(null=True)

    def get_parameters(self):
        return json.loads(self.amcat_parameters)

    def get_articleset_ids(self):
        return list(map(int, self.get_parameters()["articlesets"]))

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
        url = "http://preview.amcat.nl/api/v4/projects/{project}/querys/{query}/?format=json"
        url = url.format(project=self.amcat_project_id, query=self.amcat_query_id)

        response = requests.get(url, cookies={
            "sessionid": settings.SESSION_ID
        })

        data = json.loads(response.content.decode('utf-8'))
        self.amcat_name = data["name"]
        self.amcat_parameters = data["parameters"]
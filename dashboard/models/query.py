from __future__ import absolute_import

import datetime
import json
from urllib.parse import urlencode

from django.db import models
from dashboard.models.user import EPOCH


def cron_to_set(cron_item):
    if cron_item == "*":
        return range(100)

    if "," in cron_item:
        return map(int, cron_item.split(","))

    if "/" in cron_item:
        _, stepsize = cron_item.split("/")
        return range(0, 100, int(stepsize))

    raise ValueError("Invalid cron item: {}".format(cron_item))


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

    refresh_interval = models.TextField(null=True)

    @staticmethod
    def get_scheduled():
        return Query.objects.filter(refresh_interval__isnull=False)

    @classmethod
    def get_scheduled_for(cls, timestamp):
        for query in cls.get_scheduled().only("refresh_interval"):
            if query.is_scheduled(timestamp):
                yield query

    def is_scheduled(self, timestamp: datetime.datetime):
        if not self.refresh_interval:
            return False

        m, h, dom, mon, dow = map(cron_to_set, self.refresh_interval.split())

        return (timestamp.minute in m and
                timestamp.hour in h and
                timestamp.day in dom and
                timestamp.month in mon and
                timestamp.weekday() in dow)

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

    def poll(self):
        from dashboard.util.api import get_session, poll  # don't move this, will result in an import cycle.

        if self.cache_uuid is None:
            raise ValueError("Can't wait when uuid=None")

        result = poll(get_session(self.system), self.cache_uuid)

        # Cache results
        self.cache = result.content.decode('utf-8')
        self.cache_timestamp = datetime.datetime.now()
        self.cache_mimetype = result.headers.get("Content-Type")

    def refresh_cache(self):
        from dashboard.util.api import get_session  # don't move this, will result in an import cycle.

        # We need to fetch it from an amcat instance
        s = get_session(self.system)

        # Start job
        s.headers["Content-Type"] = "application/x-www-form-urlencoded"
        url = "{host}/api/v4/query/{script}?format=json&project={project}&sets={sets}&jobs={jobs}".format(**{
            "sets": ",".join(map(str, self.get_articleset_ids())),
            "jobs": ",".join(map(str, self.get_codingjob_ids())),
            "project": self.amcat_project_id,
            "query": self.amcat_query_id,
            "script": self.get_script(),
            "host": self.system.hostname
        })

        self.clear_cache()

        response = s.post(url, data=urlencode(self.get_parameters(), True))
        uuid = json.loads(response.content.decode("utf-8"))["uuid"]
        self.cache_uuid = uuid
        self.save()

        # We need to wait for the result..
        self.poll()

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



from __future__ import absolute_import

import datetime
import json
from _sha512 import sha512
from collections import defaultdict
from urllib.parse import urlencode

from django.db import models

from dashboard.models.user import EPOCH
from dashboard.util import itertools
from dashboard.util.api import get_session, poll


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
    amcat_options = models.TextField(null=True)

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

    def get_url_kwargs(self):
        return {
            "sets": ",".join(map(str, self.get_articleset_ids())),
            "jobs": ",".join(map(str, self.get_codingjob_ids())),
            "project": self.amcat_project_id,
            "query": self.amcat_query_id,
            "script": self.get_script(),
            "host": self.system.hostname
        }

    def get_articleset_ids(self):
        return list(map(int, self.get_parameters()["articlesets"]))

    def get_codingjob_ids(self):
        return list(map(int, self.get_parameters().get("codingjobs", [])))

    def get_script(self):
        return self.get_parameters()["script"]

    def get_output_type(self):
        return self.get_parameters()["output_type"]

    def get_options(self):
        return json.loads(self.amcat_options) if self.amcat_options is not None else None

    def refresh_cache(self):
        for cache in QueryCache.objects.filter(query=self):
            cache.refresh_cache()

    def clear_cache(self):
        QueryCache.objects.filter(query=self).update(
            cache_uuid=None,
            cache_tag=None,
            cache=None,
        )

    def update(self):
        self._update_params()
        self._update_options()

    def _update_params(self):
        url = "{host}/api/v4/projects/{project}/querys/{query}/?format=json"
        url = url.format(
            project=self.system.project_id,
            query=self.amcat_query_id,
            host=self.system.hostname
        )

        data = json.loads(get_session(self.system).get(url).content.decode('utf-8'))
        self.amcat_name = data["name"]
        self.amcat_parameters = data["parameters"]

    def _update_options(self):
        url = "{host}/api/v4/query/{script}?format=json&sets={sets}&jobs={jobs}&project={project}"
        url = url.format(**self.get_url_kwargs())

        r = get_session(self.system).options(url)
        if r.status_code >= 400:
            self.amcat_options = None
        else:
            try:
                text = r.content.decode('utf-8')
                json.loads(text)
            except json.JSONDecodeError:
                return
            self.amcat_options = text


class QueryCache(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    page = models.ForeignKey('dashboard.Page', on_delete=models.CASCADE)

    cache = models.TextField(null=True)
    cache_tag = models.TextField(null=True, max_length=36)
    cache_timestamp = models.DateTimeField(default=EPOCH)
    cache_mimetype = models.TextField(null=True)
    cache_uuid = models.TextField(null=True)

    refresh_interval = models.TextField(null=True)

    @property
    def system(self):
        return self.query.system

    def get_filters(self):
        query_filters = json.loads(self.query.get_parameters()['filters'])
        global_filters = self.query.system.get_global_filters()

        page_filters = self.page.filters

        filtersets = (query_filters, global_filters, page_filters)
        filters = defaultdict(set)
        for field, values in (item for fs in filtersets for item in fs.items()):
            filters[field] |= set(values)

        filters = {k: sorted(v) for k, v in filters.items()}  # sorted is important here to ensure consistent cache tags

        return filters

    def get_parameters(self):
        query_params = self.query.get_parameters()
        query_params['filters'] = json.dumps(self.get_filters(), ensure_ascii=True, sort_keys=True)
        return query_params

    def get_query_tag(self):
        """ Creates a unique tag for these parameters."""
        url = self.Urls.task.format(**self.query.get_url_kwargs())
        query_params = self.get_parameters()
        key = json.dumps((self.query_id, url, query_params), ensure_ascii=True, sort_keys=True).encode('ascii')
        return sha512(key).hexdigest()[:36]

    def is_valid(self):
        return self.cache_uuid and self.cache and self.cache_tag == self.get_query_tag()

    def poll(self):
        if self.cache_uuid is None:
            raise ValueError("Can't wait when uuid=None")

        result = poll(get_session(self.query.system), self.cache_uuid)

        # Cache results
        self.cache_tag = self.get_query_tag()
        self.cache = result.content.decode('utf-8')
        self.cache_timestamp = datetime.datetime.now()
        self.cache_mimetype = result.headers.get("Content-Type")

    def refresh_cache(self):
        # We need to fetch it from an amcat instance
        s = get_session(self.system)

        # Start job
        s.headers["Content-Type"] = "application/x-www-form-urlencoded"
        url = self.Urls.task.format(**self.query.get_url_kwargs())
        query_params = self.get_parameters()

        data = urlencode(query_params, True)

        response = s.post(url, data=data)
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

    class Urls:
        task = "{host}/api/v4/query/{script}?format=json&project={project}&sets={sets}&jobs={jobs}"
        query = "{host}/api/v4/projects/{project}/querys/{query}/?format=json"

    class Meta:
        app_label = "dashboard"
        db_table = "query_cache"
        unique_together = ("query", "page")

from __future__ import absolute_import

import datetime
import json
import re
from _sha512 import sha512
from collections import defaultdict
from io import StringIO
from urllib.parse import urlencode

from django.db import models

from dashboard.models.user import EPOCH
from dashboard.util import itertools
from dashboard.util.api import get_session, poll


def cron_to_set(cron_item):
    if cron_item.isdigit():
        return [int(cron_item)]
    
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

    amcat_query_id = models.IntegerField()

    amcat_name = models.TextField()
    amcat_parameters = models.TextField()
    amcat_archived = models.BooleanField()

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
    def _apply_query_override(self, query: str, query_override):
        split_re = re.compile('[\t|#]')
        newquery = StringIO()
        if not query.strip():
            return query_override
        for q in query.splitlines():
            if q:
                try:
                    prefix, query_body = split_re.split(q, 1)
                except ValueError:
                    prefix, query_body = None, q

                if prefix:
                    separator = q[len(prefix)]
                    newquery.write(prefix + separator)

                newquery.write("(({}) AND ({}))".format(query_body, query_override))
            newquery.write("\n")
        return newquery.getvalue()

    def _apply_date_override(self, relative_date: str, date_override):
        if date_override == "Gisteren":
            date_override = "-86400"
        if date_override =="Laatste week":
            date_override = "-604800"
        if date_override == "Laatste twee weken":
            date_override = "-1209600"
        if date_override =="Laatste maand":
            date_override = "-2592000"
        if date_override == "Laatste drie maanden":
            date_override = "-7776000"
        if date_override == "Laatste half jaar":
            date_override = "-15552000"
        if date_override == "Laatste jaar":
            date_override = "-31536000"
        newdate = date_override
        return newdate

    def get_parameters(self, query_override=None, extra_options=None, date_override=None):
        parameters = json.loads(self.amcat_parameters)
        if query_override:
            parameters['query'] = self._apply_query_override(parameters['query'], query_override)
        if extra_options:
            parameters.update(extra_options)
        if date_override:
            parameters['datetype'] = 'relative'
            parameters['relative_date'] = 'relative'
            parameters['relative_date'] = self._apply_date_override(parameters['relative_date'], date_override)
            if 'end_date' in parameters:
                del parameters['end_date']
            if 'start_date' in parameters:
                del parameters['start_date']
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
        if self.amcat_options is None:
            self.update_options()
            self.save()
        try:
            return json.loads(self.amcat_options)
        except json.JSONDecodeError:
            return None

    def refresh_cache(self):
        for cache in QueryCache.objects.filter(query=self):
            cache.refresh_cache()

    def clear_cache(self):
        QueryCache.objects.filter(query=self).update(
            cache_uuid=None,
            cache_timestamp=EPOCH,
            cache_tag=None,
            cache=None,
        )

    def update(self):
        self.update_params()
        self.update_options()

    def update_params(self):
        url = "{host}/api/v4/projects/{project}/querys/{query}/?format=json"
        url = url.format(
            project=self.system.project_id,
            query=self.amcat_query_id,
            host=self.system.hostname
        )

        data = json.loads(get_session(self.system).get(url).content.decode('utf-8'))
        self.amcat_name = data["name"]
        self.amcat_parameters = data["parameters"]

    def update_options(self):
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

    class Meta:
        unique_together = ("system", "amcat_query_id")


class QueryCache(models.Model):
    """ A persistent cache for queries. Does not expire or get evicted. """

    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    page = models.ForeignKey('dashboard.Page', on_delete=models.CASCADE)

    cache = models.TextField(null=True)
    cache_tag = models.TextField(null=True, max_length=36)
    cache_timestamp = models.DateTimeField(default=EPOCH)
    cache_mimetype = models.TextField(null=True)
    cache_uuid = models.TextField(null=True, db_index=True)

    refresh_interval = models.TextField(null=True)

    @property
    def system(self):
        return self.query.system

    def get_filters(self, extra_filters=None):
        query_filters = json.loads(self.query.get_parameters()['filters'])
        global_filters = self.query.system.get_global_filters()

        page_filters = self.page.filters

        if not isinstance(extra_filters, dict):
            extra_filters = {}

        filters = {}
        for filterset in (query_filters, global_filters, page_filters, extra_filters):
            for field, values in filterset.items():
                if field in filters:
                    filters[field] &= set(values)
                else:
                    filters[field] = set(values)

        filters = {k: sorted(v) for k, v in filters.items()}  # sorted is important here to ensure consistent cache tags
        return filters

    def get_parameters(self, query_override=None, extra_options=None, extra_filters=None, date_override=None):
        query_params = self.query.get_parameters(query_override=query_override, extra_options=extra_options, date_override=date_override)
        query_params['filters'] = json.dumps(self.get_filters(extra_filters=extra_filters),
                                             ensure_ascii=True,
                                             sort_keys=True)
        return query_params

    def get_query_tag(self, query_override=None, extra_filters=None, date_override=None):
        """ Creates a unique tag for these parameters."""
        url = self.Urls.task.format(**self.query.get_url_kwargs())
        query_params = self.get_parameters(query_override=query_override, extra_filters=extra_filters, date_override=date_override)
        key = json.dumps((self.query_id, url, query_params), ensure_ascii=True, sort_keys=True).encode('ascii')
        return sha512(key).hexdigest()[:36]

    def is_valid(self, query_override=None, date_override=None):
        return self.cache_uuid and self.cache and self.cache_tag == self.get_query_tag(query_override=query_override, date_override=date_override)

    def poll_once(self, uuid=None):
        if uuid is None:
            uuid = self.cache_uuid

        session = get_session(self.query.system)
        status, result = session.poll_once(uuid)
        return status, result

    def get_query_result(self, uuid=None):
        if uuid is None:
            uuid = self.cache_uuid

        session = get_session(self.query.system)
        status, result = session.get_task_result(uuid)
        return status, result

    def poll(self, uuid=None, save_result=False):
        """ Poll for """
        if uuid is None:
            uuid = self.cache_uuid

        if uuid is None:
            raise ValueError("Can't wait when uuid=None")

        result = poll(get_session(self.query.system), uuid)

        cache = result.content.decode('utf-8')
        mimetype = result.headers.get("Content-Type")
        if save_result:
            self.cache_tag = self.get_query_tag()
            self.cache = cache
            self.cache_timestamp = datetime.datetime.now()
            self.cache_mimetype = mimetype
            self.save()

        return cache, mimetype

    def start_task(self, query_override=None, extra_options=None, extra_filters=None, date_override=None):
        # We need to fetch it from an amcat instance
        s = get_session(self.system)

        # Start job
        s.headers["Content-Type"] = "application/x-www-form-urlencoded"
        url = self.Urls.task.format(**self.query.get_url_kwargs())
        query_params = self.get_parameters(query_override=query_override, extra_options=extra_options, extra_filters=extra_filters, date_override=date_override)

        data = urlencode(query_params, True)

        response = s.post(url, data=data)
        response.raise_for_status()
        uuid = json.loads(response.content.decode("utf-8"))["uuid"]
        return uuid

    def refresh_cache(self):
        uuid = self.start_task()
        self.cache_uuid = uuid
        self.save()

        # We need to wait for the result..
        self.poll(save_result=True)

    def clear_cache(self):
        self.cache = None
        self.cache_timestamp = EPOCH
        self.cache_mimetype = None
        self.cache_uuid = None

    @property
    def content_size(self):
        return len(self.cache) if self.cache else 0

    def __repr__(self):
        return "<{} {} query={}>".format(self.__class__.__name__, self.id, self.query_id)

    def __str__(self):
        return repr(self)

    class Urls:
        task = "{host}/api/v4/query/{script}?format=json&project={project}&sets={sets}&jobs={jobs}"
        query = "{host}/api/v4/projects/{project}/querys/{query}/?format=json"

    class Meta:
        app_label = "dashboard"
        unique_together = ("query", "page")

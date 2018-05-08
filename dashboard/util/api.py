from __future__ import absolute_import
import json

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import requests

from dashboard.models.system import System

TASK_URL = "{host}/api/v4/task?uuid={uuid}&format=json"
TASKRESULT_URL = "{host}/api/v4/taskresult/{uuid}?format=json"


class STATUS:
    INPROGRESS = "INPROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILURE"
    PENDING = "PENDING"


class ApiSession(requests.Session):
    def __init__(self, *, system: System):
        super().__init__()
        self.system = system
        token = system.get_api().token  # refreshes token as side effect

        self.headers["X-CSRFTOKEN"] = self.cookies.get("csrftoken")
        self.headers["AUTHORIZATION"] = "Token {}".format(token)

    def poll(self, uuid, timeout=0.2, max_timeout=2):
        response = self.get(TASK_URL.format(uuid=uuid, host=self.system.hostname))
        task = json.loads(response.content.decode("utf-8"))
        status = task["results"][0]["status"]

        if status in (STATUS.INPROGRESS, STATUS.PENDING):
            return self.poll(uuid, timeout=min(timeout * 2, max_timeout))
        elif status == STATUS.FAILED:
            raise ValueError("Task {!r} failed.".format(uuid))
        elif status == STATUS.SUCCESS:
            return self.get(TASKRESULT_URL.format(uuid=uuid, host=self.system.hostname))
        else:
            raise ValueError("Unknown status value {!r} returned.".format(status))

    def start_task(self, query):
        if query.cache_uuid is not None:
            return query.cache_uuid

        # Start job
        self.headers["Content-Type"] = "application/x-www-form-urlencoded"
        url = "{host}/api/v4/query/{script}?format=json&project={project}&sets={sets}".format(**{
            "sets": ",".join(map(str, query.get_articleset_ids())),
            "project": query.amcat_project_id,
            "query": query.amcat_query_id,
            "script": query.get_script(),
            "host": self.system.hostname
        })

        response = self.post(url, data=urlencode(query.get_parameters(), True))
        uuid = json.loads(response.content.decode("utf-8"))["uuid"]

        return uuid


def poll(session, *args, **kwargs):
    return session.poll(*args, **kwargs)


def start_task(session, *args, **kwargs):
    return session.start_task(*args, **kwargs)


def get_session(system):
    return ApiSession(system=system)

import json

from urllib.parse import urlencode
from django.conf import settings
import requests

PREVIEW_URL = "http://preview.amcat.nl/api/v4/"
TASK_URL = PREVIEW_URL + "task?uuid={uuid}&format=json"
TASKRESULT_URL = PREVIEW_URL + "taskresult/{uuid}?format=json"


class STATUS:
    INPROGRESS = "INPROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILURE"
    PENDING = "PENDING"

def poll(session, uuid, timeout=0.2, max_timeout=2):
    response = session.get(TASK_URL.format(uuid=uuid))
    task = json.loads(response.content.decode("utf-8"))
    status = task["results"][0]["status"]

    if status in (STATUS.INPROGRESS, STATUS.PENDING):
        return poll(session, uuid, timeout=min(timeout * 2, max_timeout))
    elif status == STATUS.FAILED:
        raise ValueError("Task {!r} failed.".format(uuid))
    elif status == STATUS.SUCCESS:
        return session.get(TASKRESULT_URL.format(uuid=uuid))
    else:
        raise ValueError("Unknown status value {!r} returned.".format(status))


def start_task(session, query):
    if query.cache_uuid is not None:
        return query.cache_uuid

    # Start job
    session.headers["Content-Type"] = "application/x-www-form-urlencoded"
    url = PREVIEW_URL + "query/{script}?format=json&project={project}&sets={sets}".format(**{
        "sets": ",".join(map(str, query.get_articleset_ids())),
        "project": query.amcat_project_id,
        "query": query.amcat_query_id,
        "script": query.get_script()
    })

    response = session.post(url, data=urlencode(query.get_parameters(), True))
    uuid = json.loads(response.content.decode("utf-8"))["uuid"]

    return uuid


def get_session():
    session = requests.Session()
    session.cookies.set("sessionid", settings.SESSION_ID, domain="preview.amcat.nl")
    session.get("http://preview.amcat.nl")
    session.headers["X-CSRFTOKEN"] = session.cookies.get("csrftoken")
    return session
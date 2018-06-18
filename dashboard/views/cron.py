import datetime

from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings

from dashboard.models import Query


def trigger(request, secret):
    if secret != settings.CRON_SECRET:
        return HttpResponseForbidden()

    queries = Query.get_scheduled_for(datetime.datetime.now())
    for query in queries:
        query.refresh_cache()
        query.save()

    return HttpResponse("OK", status=200)

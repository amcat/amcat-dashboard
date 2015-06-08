import json
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from dashboard.models import Page, System, Query


def import_query(request):
    pass

def serialise_query(query):
    return {
        "id": query.id,
        "amcat_query_id": query.amcat_query_id,
        "amcat_name": query.amcat_name,
        "amcat_parameters": query.amcat_parameters
    }

def serialise_queries(queries):
    return map(serialise_query, queries)

def synchronise_queries(request):
    System.load().synchronise_queries()
    queries = list(serialise_queries(Query.objects.order_by("amcat_name")))
    return HttpResponse(json.dumps(queries), content_type="application/json")

def page(request, page_id):
    page = Page.objects.get(id=page_id)
    rows = page.get_cells(select_related=("row", "query"))

    page_json = json.dumps({
        "name": page.name,
        "icon": page.icon,
        "visibible": page.visible,
        "rows": tuple(rows.items())
    })

    queries = Query.objects.only("amcat_name", "id").order_by("amcat_name")

    return render(request, "dashboard/edit.html", locals())

def index(request):
    if not Page.objects.exists():
        page = Page.objects.create(name="Default", visible=False, ordernr=0)
    else:
        page = Page.objects.all()[0]

    return redirect(reverse("dashboard:edit-page", kwargs={"page_id": page.id}))
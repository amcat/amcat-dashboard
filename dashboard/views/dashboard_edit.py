from itertools import chain, count
import json
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
import time
from dashboard.models import Page, System, Query, Row, Cell
from dashboard.util.django import bulk_insert_returning_ids


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

@transaction.atomic
def save_rows(request, page_id):
    page = Page.objects.get(id=page_id)

    rows = json.loads(request.body.decode("utf-8"))

    # Remove existing rows and cells
    row_ids = set(page.cells.values_list("row__id", flat=True))
    Row.objects.filter(id__in=row_ids).delete()
    page.cells.all().delete()

    # Insert new rows
    new_rows = [Row(ordernr=n) for n in range(len(rows))]
    new_rows = bulk_insert_returning_ids(new_rows)

    queries = Query.objects.only("id").in_bulk([q["query_id"] for q in chain(*rows)])

    cells = []
    for row, cols in zip(new_rows, rows):
        for i, col in zip(count(), cols):
            query = queries[int(col["query_id"])]
            width = col["width"]
            cells.append(Cell(width=width, query=query, page=page, row=row, ordernr=i))

    Cell.objects.bulk_create(cells)

    return HttpResponse("OK", status=201)


def page(request, page_id):
    page = Page.objects.get(id=page_id)
    rows = page.get_cells(select_related=("row", "query"))

    page_json = json.dumps({
        "name": page.name,
        "icon": page.icon,
        "visibible": page.visible,
        #"rows": tuple(rows.items())
    })

    queries = Query.objects.only("amcat_name", "id").order_by("amcat_name")

    return render(request, "dashboard/edit.html", locals())

def index(request):
    if not Page.objects.exists():
        page = Page.objects.create(name="Default", visible=False, ordernr=0)
    else:
        page = Page.objects.all()[0]

    return redirect(reverse("dashboard:edit-page", kwargs={"page_id": page.id}))
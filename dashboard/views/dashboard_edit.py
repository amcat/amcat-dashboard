import json
from itertools import chain, count
from operator import itemgetter

from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import FormView

from dashboard.models import Page, Query, Row, Cell, HighchartsTheme, QueryCache
from dashboard.models.dashboard import HIGHCHARTS_CUSTOM_PROPERTIES
from dashboard.util.django import bulk_insert_returning_ids
from dashboard.util.itertools import split


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
    system = request.user.system
    system.synchronise_queries()
    queries = list(serialise_queries(Query.objects.filter(system=system).order_by("amcat_name")))
    return HttpResponse(json.dumps(queries), content_type="application/json")


OK_CREATED = HttpResponse("OK", status=201)


@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def save_rows(request, page_id):
    page = Page.objects.get(id=page_id)

    rows = json.loads(request.body.decode("utf-8"))

    # Remove existing rows and cells
    row_ids = set(page.cells.values_list("row__id", flat=True))
    Row.objects.filter(id__in=row_ids).delete()
    page.cells.all().delete()

    # Insert new rows
    if not rows:
        return OK_CREATED

    new_rows = [Row(ordernr=n) for n in range(len(rows))]
    new_rows = bulk_insert_returning_ids(new_rows)

    queries = Query.objects.only("id", "refresh_interval").in_bulk([q["query_id"] for q in chain(*rows)])
    themes = HighchartsTheme.objects.only("id").in_bulk([t["theme_id"] for t in chain(*rows) if t["theme_id"]])
    cells = []
    for row, cols in zip(new_rows, rows):
        for i, col in zip(count(), cols):
            query = queries[int(col["query_id"])]
            link = col["link"]
            if not link:
                link = None
            if col['theme_id']:
                theme = themes[int(col['theme_id'])]
            else:
                theme = None
            width = col["width"]

            customize = {k: v for k, v in col["customize"].items()
                         if isinstance(k, str) and k
                         if isinstance(v, (str, int, float, bool))}

            if query.refresh_interval != col['refresh_interval']:
                query.refresh_interval = col['refresh_interval']
                query.save()

            cells.append(
                Cell(
                    width=width,
                    query=query,
                    title=col['title'],
                    page=page,
                    row=row,
                    ordernr=i,
                    theme=theme,
                    customize=customize,
                    link=link,
                )
            )
            cells[-1].clean()

    Cell.objects.bulk_create(cells)
    QueryCache.objects.filter(page_id=page_id).exclude(query__cells__page_id=page_id).delete()
    return OK_CREATED


@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def save_menu(request):
    system = request.user.system
    pages_qs = Page.objects.filter(system=system)
    pages = json.loads(request.body.decode("utf-8"))
    existing_pages, new_pages = split(itemgetter("id"), pages)

    # We must use delete() on a single Page objects, as it deletes associated rows/cells
    existing_pages_ids = list(map(itemgetter("id"), existing_pages))

    for page in pages_qs.exclude(id__in=existing_pages_ids):
        Page.objects.only("id").get(id=page.id).delete()

    for page in existing_pages:
        page_obj = Page.objects.get(pk=page["id"])
        page_obj.name = page["name"]
        page_obj.visible = page["visible"]
        page_obj.icon = page["icon"]
        page_obj.ordernr = pages.index(page)
        page_obj.save()

    if not pages:
        return OK_CREATED

    Page.objects.bulk_create([Page(ordernr=pages.index(page), system=system, **page) for page in new_pages])
    return OK_CREATED


@user_passes_test(lambda u: u.is_superuser)
def menu(request):
    system = request.user.system
    pages = Page.objects.filter(system=system)
    pages = json.dumps([{
        "id": page.id,
        "icon": page.icon,
        "visible": page.visible,
        "name": page.name
    } for page in pages])
    editing = True
    return render(request, "dashboard/edit_menu.html", locals())

@user_passes_test(lambda u: u.is_superuser)
def page(request, page_id):
    system = request.user.system
    page = Page.objects.get(id=page_id)
    # TODO: we only need refresh_interval info from query
    rows = page.get_cells(select_related=("query",))

    page_json = page.serialise()
    page_json.update({
        "rows": [[{
            "width": cell.width,
            "query_id": cell.query_id,
            "theme_id": cell.theme_id,
            "title": cell.title,
            "refresh_interval": cell.query.refresh_interval,
            "customize": cell.customize,
            "link": cell.link,
        }
            for cell in cells]
            for row, cells in rows.items()]
    })

    page_json = json.dumps(page_json)

    # Show only queries that are either active/non-archived in AmcAT or used in a cell in this system
    used_query_ids = {c.query_id for c in Cell.objects.filter(page__system_id=system.id)}
    queries = (Query.objects.filter(Q(amcat_archived=False) | Q(pk__in=used_query_ids), system=system)
               .only("amcat_name", "amcat_query_id", "id").order_by("-amcat_query_id", ))
    pages = Page.objects.filter(system=system)
    customizations = HIGHCHARTS_CUSTOM_PROPERTIES
    return render(request, "dashboard/edit_page.html", locals())


class CopyPageFormView(FormView):
    class form_class(forms.Form):
        page = forms.ModelChoiceField(queryset=Page.objects.all())

    def form_valid(self, form):
        page = form.cleaned_data['page']
        page.create_copy()
        return redirect(reverse("dashboard:edit-menu"))


@user_passes_test(lambda u: u.is_superuser)
def index(request):
    system = request.user.system
    pages = Page.objects.filter(system=system)
    if not pages.exists():
        page = Page.objects.create(name="Default", visible=False, ordernr=0, system=system)
    else:
        page = pages.first()

    return redirect(reverse("dashboard:edit-page", kwargs={"page_id": page.id}))
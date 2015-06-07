import json
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from dashboard.models import Page


def import_query(request):
    pass

def page(request, page_id):
    page = Page.objects.get(id=page_id)
    rows = page.get_cells(select_related=("row", "query"))

    page_json = json.dumps({
        "name": page.name,
        "icon": page.icon,
        "visibible": page.visible,
        "rows": tuple(rows.items())
    })

    return render(request, "dashboard/edit.html", locals())

def index(request):
    if not Page.objects.exists():
        page = Page.objects.create(name="Default", visible=False, ordernr=0)
    else:
        page = Page.objects.all()[0]

    return redirect(reverse("dashboard:edit-page", kwargs={"page_id": page.id}))
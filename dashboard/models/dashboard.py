from collections import OrderedDict
from django.db import models
from dashboard.models.query import Query

def get_active_queries():
    query_ids = Cell.objects.values_list("query__id", flat=True)
    return Query.objects.get(id__in=set(query_ids))

class Page(models.Model):
    name = models.TextField()
    icon = models.TextField(null=True)
    ordernr = models.PositiveSmallIntegerField(db_index=True, unique=True)
    visible = models.BooleanField(default=False)

    def get_cells(self, select_related=("row",)):
        """
        Efficiently determine a mapping from row to cells.

        @param select_related: prefetch fields on each Cell
        @return: OrderedDictionary(row -> [cell])
        """
        odict = OrderedDict()
        for cell in self.cells.select_related(*select_related):
            if cell.row not in odict:
                odict[cell.row] = []
            odict[cell.row].append(cell)
        return odict

    class Meta:
        app_label = "dashboard"
        ordering = ["ordernr"]

class Row(models.Model):
    ordernr = models.PositiveSmallIntegerField(db_index=True)

    class Meta:
        app_label = "dashboard"
        ordering = ["ordernr"]

class Cell(models.Model):
    """A cell represents a 'tile' holding a query on the dashboard."""
    query = models.ForeignKey(Query, related_name="cells")
    page = models.ForeignKey(Page, related_name="cells")

    # You may expect to find Page.rows().cells(), but storing it this way is more
    # efficient as we can fetch a single page with one query.
    row = models.ForeignKey(Row, related_name="cells")

    width = models.PositiveSmallIntegerField(max_length=12)
    ordernr = models.PositiveSmallIntegerField(db_index=True)

    class Meta:
        app_label = "dashboard"
        ordering = ["row__ordernr", "ordernr"]
        unique_together = (("page", "ordernr"),)
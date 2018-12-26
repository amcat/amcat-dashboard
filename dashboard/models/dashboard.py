from __future__ import absolute_import

import copy
import itertools
import json
import re
from collections import OrderedDict, namedtuple, defaultdict

from django.contrib.postgres.fields import JSONField
from django.core.validators import RegexValidator
from django.db import models
from django.db import transaction

from dashboard.models.query import Query
from dashboard.util.validators import HighchartsCustomizationValidator


class Filter(models.Model):
    field_re = "[a-z0-9]+(_[a-z]+)?"

    system = models.ForeignKey('dashboard.System', on_delete=models.CASCADE)
    field = models.CharField(validators=[RegexValidator(field_re, flags=re.IGNORECASE)], max_length=100)
    value = models.CharField(max_length=200)

    class Meta:
        app_label = "dashboard"
        ordering = ("field", "value")


def get_active_queries():
    query_ids = Cell.objects.values_list("query__id", flat=True)
    return Query.objects.get(id__in=set(query_ids))


class Page(models.Model):
    system = models.ForeignKey('dashboard.System', on_delete=models.CASCADE)
    name = models.TextField()
    icon = models.TextField(null=True)
    ordernr = models.PositiveSmallIntegerField(db_index=True)
    visible = models.BooleanField(default=False)

    @property
    def filters(self):
        return {}

    def serialise(self):
        return dict(name=self.name, icon=self.icon, visible=self.visible)

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

    @transaction.atomic
    def delete(self, using=None):
        cells = self.cells.only("id", "row_id")
        Row.objects.filter(id__in={c.row_id for c in cells}).delete()
        Cell.objects.filter(id__in={c.id for c in cells}).delete()
        super(Page, self).delete(using=using)

    @transaction.atomic
    def create_copy(self):
        page = copy.deepcopy(self)
        page.pk = None
        page.name = self.get_unique_copy_name()
        page.ordernr = page.system.page_set.order_by('-ordernr').first().ordernr + 1
        page.save()

        cells = []
        rows = []
        for row, row_cells in self.get_cells().items():
            row.pk = None
            for cell in row_cells:
                cell.pk = None
                cell.page = page

            cells.extend(row_cells)
            rows.append(row)

        Cell.objects.bulk_create(cells)
        Row.objects.bulk_create(rows)
        return page, cells, rows

    def get_unique_copy_name(self):
        names = itertools.chain(
            ['{} (copy)'.format(self.name)],
            ('{} (copy {})'.format(self.name, i) for i in itertools.count(start=2))
        )
        existing = set(Page.objects.filter(system=self.system).values_list('name', flat=True))
        for name in names:
            if name not in existing:
                return name

    def __repr__(self):
        return "<{cls.__name__}: {self.name}>".format(cls=self.__class__, self=self)

    class Meta:
        app_label = "dashboard"
        ordering = ["ordernr"]
        unique_together = ('system', 'ordernr')


class Row(models.Model):
    ordernr = models.PositiveSmallIntegerField(db_index=True)

    class Meta:
        app_label = "dashboard"
        ordering = ["ordernr"]


HighchartsProperty = namedtuple("HighchartsProperty", ("type", "form_type", "label", "default", "placeholder"))

HIGHCHARTS_CUSTOM_PROPERTIES = (
    ("yAxis.0.title.text", HighchartsProperty(str, "text", "y-Axis label", None, "<automatic>")),
    ("yAxis.1.title.text", HighchartsProperty(str, "text", "secondary y-Axis label", None, "<automatic>")),
    ("series.0.tooltip.valueDecimals", HighchartsProperty(int, "number", "Tooltip decimals", None, "<automatic>")),
    ("series.1.tooltip.valueDecimals", HighchartsProperty(int, "number", "Secondary tooltip decimals", None, "<automatic>")),
    ("legend.enabled", HighchartsProperty(bool, "checkbox", "Enable legend", True, "true")),
    ("series.0.name", HighchartsProperty(str, "text", "Series name", None, "<automatic>")),
    ("series.1.name", HighchartsProperty(str, "text", "Secondary series name", None, "<automatic>")),
    ("credits.enabled", HighchartsProperty(bool, "checkbox", "Credits enabled", False, "false")),
    ("credits.text", HighchartsProperty(str, "text", "Credits text", None, "e.g. Highcharts.com")),
    ("credits.href", HighchartsProperty(str, "text", "Credits url", None, "e.g. http://www.highcharts.com")),
)


class Cell(models.Model):
    """A cell represents a 'tile' holding a query on the dashboard."""
    query = models.ForeignKey(Query, related_name="cells")
    page = models.ForeignKey(Page, related_name="cells")

    title = models.CharField(max_length=250, null=True)
    theme = models.ForeignKey('dashboard.HighchartsTheme', related_name="cells", on_delete=models.SET_NULL, null=True)
    customize = JSONField(validators=(HighchartsCustomizationValidator(HIGHCHARTS_CUSTOM_PROPERTIES),), default={})

    # You may expect to find Page.rows().cells(), but storing it this way is more
    # efficient as we can fetch a single page with one query.
    row = models.ForeignKey(Row, related_name="cells")  # (isn't this just a glorified integer field?)

    width = models.PositiveSmallIntegerField()
    ordernr = models.PositiveSmallIntegerField(db_index=True)

    def get_highcharts_custom_json(self):

        recursive_defaultdict = lambda: defaultdict(recursive_defaultdict)
        root = recursive_defaultdict()

        for k, spec in HIGHCHARTS_CUSTOM_PROPERTIES:
            v = self.customize.get(k, spec.default)
            if v is None:
                continue

            path = k.split('.')
            node = root
            for el in path[:-1]:
                node = node[el]
            node[path[-1]] = spec.type(v)
        return json.dumps(root)

    def get_title(self):
        return self.title or self.query.amcat_name

    class Meta:
        app_label = "dashboard"
        ordering = ["row__ordernr", "ordernr"]
        unique_together = (("page", "row", "ordernr"),)


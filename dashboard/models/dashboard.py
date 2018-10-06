from __future__ import absolute_import

import json
import re
from collections import OrderedDict, namedtuple, defaultdict

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db import transaction

from dashboard.models.query import Query


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


def page_filters_validator(val):
    if not isinstance(val, dict):
        raise ValidationError
    if not all(isinstance(v, list) for v in val.values()):
        raise ValidationError
    if not all(isinstance(v, str) for vs in val.values() for v in vs):
        raise ValidationError

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
    ("legend.enabled", HighchartsProperty(bool, "checkbox", "Enable legend", True, "true")),
    ("series.0.name", HighchartsProperty(str, "text", "First series name", None, "<automatic>")),
    ("series.1.name", HighchartsProperty(str, "text", "Second series name", None, "<automatic>")),
    ("credits.enabled", HighchartsProperty(bool, "checkbox", "Credits enabled", False, "false")),
    ("credits.text", HighchartsProperty(str, "text", "Credits text", None, "e.g. Highcharts.com")),
    ("credits.href", HighchartsProperty(str, "text", "Credits url", None, "e.g. http://www.highcharts.com")),
)

def highcharts_customization_dict_validator(value):
    errors = []
    custom_props = dict(HIGHCHARTS_CUSTOM_PROPERTIES)
    if not isinstance(value, dict):
        raise ValidationError("Root element must be a dict, got {}".format(type(value)))

    for k, v in value.items():
        try:
            prop = custom_props[k]
        except KeyError:
            errors.append(ValidationError("Unknown property {}".format(k)))
            continue
        if not isinstance(v, prop.type):
            raise ValidationError("Invalid type for {}, expected {!s}, got {!s}".format(k, prop.type, type(v)))

    if errors:
        raise ValidationError(errors)
        

class Cell(models.Model):
    """A cell represents a 'tile' holding a query on the dashboard."""
    query = models.ForeignKey(Query, related_name="cells")
    page = models.ForeignKey(Page, related_name="cells")

    title = models.CharField(max_length=250, null=True)
    theme = models.ForeignKey('dashboard.HighchartsTheme', related_name="cells", on_delete=models.SET_NULL, null=True)
    customize = JSONField(validators=(highcharts_customization_dict_validator,), default={})

    # You may expect to find Page.rows().cells(), but storing it this way is more
    # efficient as we can fetch a single page with one query.
    row = models.ForeignKey(Row, related_name="cells")

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


import json

from django.db import models

COLORS_DEFAULT = "#7cb5ec #434348 #90ed7d #f7a35c #8085e9 #f15c80 #e4d354 #2b908f #f45b5b #91e8e1"


def colors_validator(value):
    return isinstance(value, str) and len(value.split(' ')) == 10


class HighchartsTheme(models.Model):

    system = models.ForeignKey('dashboard.System', on_delete=models.CASCADE)
    name = models.TextField(max_length=40)

    y_axis_line_width = models.IntegerField(default=0)
    y_axis_has_line_color = models.BooleanField(default=False)
    y_label_has_line_color = models.BooleanField(default=False)

    colors = models.TextField(validators=(colors_validator,), default=COLORS_DEFAULT)



    def theme_args(self):
        colors = self.colors.split(" ")[:10]
        w = self.y_axis_line_width

        def titlestyle(color):
            return {"style": {"color": color}} if self.y_axis_has_line_color else {}

        return json.dumps({
            "colors": colors,
            "yAxis": [{"lineColor": c, "lineWidth": w, "title": titlestyle(c)} for c in colors[0:2]]
        })

    class Meta:
        app_label = 'dashboard'
        unique_together = ("name", "system")
        ordering = ('id',)

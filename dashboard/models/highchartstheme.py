import json
import logging
from base64 import b64encode, urlsafe_b64encode, b32encode
from hashlib import sha512

import scss
import scss.errors
from django.contrib.postgres.fields import JSONField
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.template.loader import render_to_string

COLORS_DEFAULT = {
    "colors": "#7cb5ec #434348 #90ed7d #f7a35c #8085e9 #f15c80 #e4d354 #2b908f #f45b5b #91e8e1",
    "backgroundColor": "#ffffff",

    "neutralColor100": "#000000",
    "neutralColor80": "#333333",
    "neutralColor60": "#666666",
    "neutralColor40": "#999999",
    "neutralColor20": "#cccccc",
    "neutralColor10": "#e6e6e6",
    "neutralColor5": "#f2f2f2",
    "neutralColor3": "#f7f7f7",

    "highlightColor100": "#003399",
    "highlightColor80": "#335cad",
    "highlightColor60": "#6685c2",
    "highlightColor20": "#ccd6eb",
    "highlightColor10": "#e6ebf5"
}


def compile_theme(scss_str, **kwargs):
    highcharts_path = finders.find('components/highcharts/css')
    r = scss.Compiler(search_path=(highcharts_path,), output_style='compressed', **kwargs).compile_string(scss_str)
    return r


def colors_validator(value):
    value = json.loads(value)
    if not isinstance(value, dict):
        raise ValidationError("Invalid colors: not an object")
    if not all(isinstance(v, str) for v in value.values()):
        raise ValidationError("Color value must be str")


class HighchartsTheme(models.Model):
    system = models.ForeignKey('dashboard.System', on_delete=models.CASCADE)
    name = models.TextField(max_length=100, validators=[RegexValidator("^[\w +_=#.,-]+$")],
                            help_text="A name for the theme. May only contain alphanumeric characters, spaces,"
                                      "or any of the following characters: -+_=#.,")

    colors = models.TextField(validators=(colors_validator,), default=json.dumps(COLORS_DEFAULT))

    namespace = models.TextField(max_length=32)
    tag = models.TextField(null=True, max_length=32, db_index=True)

    def _namespaced_scss(self):
        return ".{} {{ {} }}".format(self.namespace, self.theme_scss())

    def save(self, *args, **kwargs):
        sha = sha512(self.colors.encode('utf-8'))
        sha.update(self.name.encode('utf-8'))
        sha.update(self.system_id.to_bytes(8, 'big'))
        self.tag = sha.hexdigest()[:32]

        sha = sha512(self.system_id.to_bytes(8, 'big'))
        sha.update(self.name.encode('utf-8'))
        self.namespace = "hc-ns-" + b32encode(sha.digest()[:10]).decode('ascii')
        super().save(*args, **kwargs)


    def theme_scss(self):
        self.full_clean()
        colors = json.loads(self.colors)
        scsstext = render_to_string('dashboard/highcharts_theme.scss.html', {"colors": dict(COLORS_DEFAULT, **colors)})
        return scsstext

    def theme_css(self):
        logging.warning('Compiling theme')
        try:
            css = compile_theme(self._namespaced_scss())
        except scss.errors.SassBaseError:
            css = '.{}:before{{content: "Theme error"; color: red;}}'.format(self.namespace)
        return css


    class Meta:
        app_label = 'dashboard'
        unique_together = ("name", "system")
        ordering = ('id',)
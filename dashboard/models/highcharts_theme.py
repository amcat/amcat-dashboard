import json
import logging
from base64 import b32encode, b16encode
from binascii import hexlify
from hashlib import sha512

from django.contrib.postgres.fields import JSONField
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.template.loader import render_to_string

COLORS_DEFAULT = "#7cb5ec #434348 #90ed7d #f7a35c #8085e9 #f15c80 #e4d354 #2b908f #f45b5b #91e8e1"


def colors_validator(value):
    return isinstance(value, str) and len(value.split(' ')) == 10


class HighchartsTheme(models.Model):
    _fallback_color = "#ff00ff"

    system = models.ForeignKey('dashboard.System', on_delete=models.CASCADE)
    name = models.TextField(max_length=40)

    colors = models.TextField(validators=(colors_validator,), default=COLORS_DEFAULT)



    def theme_args(self):
        colors = self.colors.split(" ")[:10]
        return json.dumps({
            "colors": colors
        })

    class Meta:
        app_label = 'dashboard'
        unique_together = ("name", "system")
        ordering = ('id',)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_auto_20150607_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='system',
            name='hostname',
            field=models.TextField(default='http://preview.amcat.nl'),
        ),
    ]

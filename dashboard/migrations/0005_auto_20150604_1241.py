# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_query'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='cache',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='query',
            name='cache_timestamp',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0)),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_auto_20150604_1241'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='cache_mimetype',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='query',
            name='cache_uuid',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='query',
            name='amcat_query_id',
            field=models.IntegerField(db_index=True, unique=True),
        ),
    ]

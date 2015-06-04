# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_auto_20150604_1317'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='amcat_project_id',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='query',
            name='amcat_query_id',
            field=models.IntegerField(db_index=True, unique=True),
        ),
    ]

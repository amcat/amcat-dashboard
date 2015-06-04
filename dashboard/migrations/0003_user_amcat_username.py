# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_auto_20150603_2224'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='amcat_username',
            field=models.TextField(null=True),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-01 11:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0021_auto_20180630_2134'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='amcat_options',
            field=models.TextField(null=True),
        ),
    ]

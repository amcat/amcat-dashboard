# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-06-21 18:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0030_query_amcat_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='system',
            name='dashboard_name',
            field=models.TextField(null=True),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-23 13:05
from __future__ import unicode_literals

import dashboard.models.dashboard
import django.contrib.postgres.fields.jsonb
from django.db import migrations

import dashboard.util.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0019_query_refresh_interval'),
    ]

    operations = [
        migrations.AddField(
            model_name='cell',
            name='customize',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}, validators=[]),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-26 18:25
from __future__ import unicode_literals

import dashboard.models.highcharts_theme
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_themes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='highchartstheme',
            name='namespace',
        ),
        migrations.RemoveField(
            model_name='highchartstheme',
            name='tag',
        ),
        migrations.AlterField(
            model_name='highchartstheme',
            name='colors',
            field=models.TextField(default='#7cb5ec #434348 #90ed7d #f7a35c #8085e9 #f15c80 #e4d354 #2b908f #f45b5b #91e8e1', validators=[dashboard.models.highcharts_theme.colors_validator]),
        ),
        migrations.AlterField(
            model_name='highchartstheme',
            name='name',
            field=models.TextField(max_length=40),
        ),
    ]
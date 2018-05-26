# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-21 20:06
from __future__ import unicode_literals

import dashboard.models.highcharts_theme
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0015_page_system'),
    ]

    operations = [
        migrations.CreateModel(
            name='HighchartsTheme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(help_text='A name for the theme. May only contain alphanumeric characters, spaces,or any of the following characters: -+_=#.,', max_length=100, validators=[django.core.validators.RegexValidator('^[\\w +_=#.,-]+$')])),
                ('colors', models.TextField(default='{"backgroundColor": "#ffffff", "colors": "#7cb5ec #434348 #90ed7d #f7a35c #8085e9 #f15c80 #e4d354 #2b908f #f45b5b #91e8e1", "highlightColor10": "#e6ebf5", "highlightColor100": "#003399", "highlightColor20": "#ccd6eb", "highlightColor60": "#6685c2", "highlightColor80": "#335cad", "neutralColor10": "#e6e6e6", "neutralColor100": "#000000", "neutralColor20": "#cccccc", "neutralColor3": "#f7f7f7", "neutralColor40": "#999999", "neutralColor5": "#f2f2f2", "neutralColor60": "#666666", "neutralColor80": "#333333"}', validators=[dashboard.models.highcharts_theme.colors_validator])),
                ('namespace', models.TextField(max_length=32)),
                ('tag', models.TextField(db_index=True, max_length=32, null=True)),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.System')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.AddField(
            model_name='cell',
            name='theme',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cells', to='dashboard.HighchartsTheme'),
        ),
        migrations.AlterUniqueTogether(
            name='highchartstheme',
            unique_together=set([('name', 'system')]),
        ),
    ]
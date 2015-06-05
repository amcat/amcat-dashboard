# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_auto_20150604_1607'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('width', models.PositiveSmallIntegerField(max_length=12)),
                ('ordernr', models.PositiveSmallIntegerField(db_index=True)),
            ],
            options={
                'ordering': ['row__ordernr', 'ordernr'],
            },
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.TextField()),
                ('icon', models.TextField(null=True)),
                ('ordernr', models.PositiveSmallIntegerField(db_index=True)),
                ('visible', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['ordernr'],
            },
        ),
        migrations.CreateModel(
            name='Row',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('ordernr', models.PositiveSmallIntegerField(db_index=True)),
            ],
            options={
                'ordering': ['ordernr'],
            },
        ),
        migrations.AddField(
            model_name='cell',
            name='page',
            field=models.ForeignKey(related_name='cells', to='dashboard.Page'),
        ),
        migrations.AddField(
            model_name='cell',
            name='query',
            field=models.ForeignKey(related_name='cells', to='dashboard.Query'),
        ),
        migrations.AddField(
            model_name='cell',
            name='row',
            field=models.ForeignKey(related_name='cells', to='dashboard.Row'),
        ),
    ]

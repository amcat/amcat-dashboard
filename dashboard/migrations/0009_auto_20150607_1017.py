# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_auto_20150605_0950'),
    ]

    operations = [
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('project_id', models.PositiveIntegerField(null=True, help_text='AmCAT project this dashboard is linked to')),
                ('project_name', models.TextField(null=True)),
                ('api_user', models.ForeignKey(to=settings.AUTH_USER_MODEL, help_text='User on whose behalf API calls are made to AmCAT')),
            ],
        ),
        migrations.AlterField(
            model_name='page',
            name='ordernr',
            field=models.PositiveSmallIntegerField(db_index=True, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='cell',
            unique_together=set([('page', 'ordernr')]),
        ),
    ]

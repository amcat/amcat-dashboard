# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_user_amcat_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('amcat_query_id', models.IntegerField()),
                ('amcat_project_id', models.IntegerField()),
                ('amcat_name', models.TextField()),
                ('amcat_parameters', models.TextField()),
            ],
        ),
    ]

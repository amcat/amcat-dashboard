# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


def get_default():
    try:
        from dashboard.models import System
        return System.objects.first().pk
    except:
        return None

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0013_remove_system_api_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='query',
            name='amcat_project_id',
        ),
        migrations.AddField(
            model_name='query',
            name='system',
            field=models.ForeignKey(default=get_default(), to='dashboard.System'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='system',
            field=models.ForeignKey(to='dashboard.System', on_delete=django.db.models.deletion.SET_NULL, null=True,
                                    default=get_default()),
        ),
        migrations.AlterField(
            model_name='user',
            name='system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='dashboard.System', null=True),
        ),
    ]

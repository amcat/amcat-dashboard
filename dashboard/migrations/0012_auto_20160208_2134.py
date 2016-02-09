# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0011_auto_20150608_1406'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='amcat_token',
        ),
        migrations.RemoveField(
            model_name='user',
            name='amcat_username',
        ),
        migrations.AddField(
            model_name='system',
            name='amcat_token',
            field=models.TextField(null=True),
        ),
    ]

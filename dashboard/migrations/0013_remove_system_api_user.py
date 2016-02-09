# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0012_auto_20160208_2134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='system',
            name='api_user',
        ),
    ]

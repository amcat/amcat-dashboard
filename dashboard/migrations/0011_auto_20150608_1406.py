# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_system_hostname'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cell',
            unique_together=set([('page', 'row', 'ordernr')]),
        ),
    ]

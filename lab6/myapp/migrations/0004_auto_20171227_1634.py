# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-27 13:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_auto_20171227_1151'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactionsmodel',
            name='accountId_from',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.AccountModel'),
        ),
    ]

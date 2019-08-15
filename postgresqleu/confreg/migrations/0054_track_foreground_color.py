# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-08-15 14:13
from __future__ import unicode_literals

from django.db import migrations, models
import postgresqleu.confreg.models


class Migration(migrations.Migration):

    dependencies = [
        ('confreg', '0053_addoption_additionaldays'),
    ]

    operations = [
        migrations.AddField(
            model_name='track',
            name='fgcolor',
            field=models.CharField(default='#000000', max_length=20, validators=[postgresqleu.confreg.models.color_validator], verbose_name='Foreground color'),
        ),
        migrations.AlterField(
            model_name='track',
            name='color',
            field=models.CharField(blank=True, max_length=20, validators=[postgresqleu.confreg.models.color_validator], verbose_name='Background color'),
        ),
    ]

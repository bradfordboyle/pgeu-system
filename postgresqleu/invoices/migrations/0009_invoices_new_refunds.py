# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-12-27 12:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0008_invoice_bcc_list'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoicerefund',
            name='invoice',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='invoices.Invoice'),
        ),
        migrations.RunSQL("UPDATE invoices_invoicerefund SET invoice_id=invoices_invoice.id FROM invoices_invoice WHERE invoices_invoice.refund_id=invoices_invoicerefund.id"),
        migrations.AlterField(
            model_name='invoicerefund',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoices.Invoice'),
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='refund',
        ),
        migrations.AlterModelOptions(
            name='invoicerefund',
            options={'ordering': ('id',)},
        )
    ]

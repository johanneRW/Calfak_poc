# Generated by Django 3.2.23 on 2023-12-14 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_appointmentseries_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='lastAppointmentImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='lastInvoiceLinesEksport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
            ],
        ),
    ]

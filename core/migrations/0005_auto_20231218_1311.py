# Generated by Django 3.2.23 on 2023-12-18 12:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_lastappointmentimport_lastinvoicelineseksport'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='system_note',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='appointments', to='core.appointmentseries'),
        ),
    ]
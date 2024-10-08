# Generated by Django 5.1 on 2024-09-02 07:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("behavioral", "0003_secameasurement"),
        ("scans", "0012_session_date_session_session_id_session_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="seca_measurement",
            field=models.ForeignKey(
                help_text="The SECA measurement associated with this session",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sessions",
                to="behavioral.secameasurement",
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="time_between_scan_and_seca",
            field=models.DurationField(
                blank=True,
                help_text="The time between the scan and the SECA measurement",
                null=True,
            ),
        ),
    ]

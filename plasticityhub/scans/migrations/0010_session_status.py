# Generated by Django 5.1 on 2024-08-30 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scans", "0009_alter_session_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="status",
            field=models.CharField(
                blank=True,
                help_text="The status of the session (e.g., complete, incomplete, canceled)",
                max_length=20,
            ),
        ),
    ]

# Generated by Django 5.1 on 2024-08-27 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scans", "0006_alter_session_scan_tag"),
    ]

    operations = [
        migrations.AlterField(
            model_name="session",
            name="scan_tag",
            field=models.CharField(
                blank=True,
                help_text="The tag associated with the scan (e.g, pre, post, during)",
                max_length=20,
            ),
        ),
    ]
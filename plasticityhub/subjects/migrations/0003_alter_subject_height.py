# Generated by Django 5.1 on 2024-08-25 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subjects", "0002_subject_age_subject_email_subject_height_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subject",
            name="height",
            field=models.FloatField(
                blank=True, help_text="Height of the subject in centimeters", null=True
            ),
        ),
    ]

# Generated by Django 5.1 on 2024-09-04 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("procedures", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="procedure",
            name="path",
            field=models.CharField(
                default="",
                help_text="The path to the procedure's output",
                max_length=255,
            ),
            preserve_default=False,
        ),
    ]

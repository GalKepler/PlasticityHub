# Generated by Django 5.1 on 2024-08-29 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("studies", "0002_lab"),
    ]

    operations = [
        migrations.AddField(
            model_name="study",
            name="lab",
            field=models.ManyToManyField(related_name="studies", to="studies.lab"),
        ),
    ]
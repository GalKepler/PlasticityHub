# Generated by Django 5.1 on 2024-09-02 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("behavioral", "0003_secameasurement"),
    ]

    operations = [
        migrations.AlterField(
            model_name="secameasurement",
            name="subject_code",
            field=models.CharField(
                blank=True,
                help_text="The subject code associated with the measurement",
                max_length=50,
                null=True,
            ),
        ),
    ]

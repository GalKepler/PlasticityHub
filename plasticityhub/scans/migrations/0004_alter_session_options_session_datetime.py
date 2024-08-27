# Generated by Django 5.1 on 2024-08-26 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0003_alter_session_condition_alter_session_group_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='session',
            options={'ordering': ['datetime'], 'verbose_name': 'Session', 'verbose_name_plural': 'Sessions'},
        ),
        migrations.AddField(
            model_name='session',
            name='datetime',
            field=models.DateTimeField(editable=False, null=True),
        ),
    ]
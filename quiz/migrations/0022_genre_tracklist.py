# Generated by Django 2.2.12 on 2020-05-14 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0021_auto_20200514_1802'),
    ]

    operations = [
        migrations.AddField(
            model_name='genre',
            name='tracklist',
            field=models.URLField(blank=True, null=True),
        ),
    ]
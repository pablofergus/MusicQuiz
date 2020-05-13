# Generated by Django 2.2.12 on 2020-05-13 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0013_game_running'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='password',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='game',
            name='private',
            field=models.BooleanField(default=False),
        ),
    ]
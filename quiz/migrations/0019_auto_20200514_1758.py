# Generated by Django 2.2.12 on 2020-05-14 15:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0018_auto_20200513_2320'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gamesettings',
            name='game_type',
        ),
        migrations.AddField(
            model_name='gamesettings',
            name='game_type',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='quiz.GameTypes'),
        ),
        migrations.RemoveField(
            model_name='gamesettings',
            name='genre',
        ),
        migrations.AddField(
            model_name='gamesettings',
            name='genre',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='quiz.Genre'),
        ),
    ]

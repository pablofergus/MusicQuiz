# Generated by Django 2.2.12 on 2020-05-08 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20200501_0205'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='song_history',
            field=models.ManyToManyField(to='quiz.Song'),
        ),
    ]

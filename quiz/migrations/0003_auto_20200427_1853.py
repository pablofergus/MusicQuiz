# Generated by Django 2.2.12 on 2020-04-27 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_auto_20200427_1726'),
    ]

    operations = [
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('picture', models.URLField()),
                ('fans', models.IntegerField()),
                ('albums', models.IntegerField()),
            ],
        ),
        migrations.RemoveField(
            model_name='song',
            name='artist',
        ),
        migrations.RemoveField(
            model_name='song',
            name='artist_picture',
        ),
        migrations.RemoveField(
            model_name='song',
            name='genre',
        ),
        migrations.AddField(
            model_name='song',
            name='artists',
            field=models.ManyToManyField(to='quiz.Artist'),
        ),
    ]

# Generated by Django 2.2.12 on 2020-05-08 12:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0008_auto_20200508_1437'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gameinfo',
            name='track',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='quiz.Song'),
        ),
    ]

# Generated by Django 3.1.6 on 2021-03-03 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0004_auto_20210303_2344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='has_time',
            field=models.BooleanField(),
        ),
    ]

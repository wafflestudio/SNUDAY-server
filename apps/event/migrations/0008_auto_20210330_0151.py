# Generated by Django 3.1.6 on 2021-03-29 16:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0007_auto_20210330_0130"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="due_time",
            field=models.TimeField(null=True),
        ),
        migrations.AlterField(
            model_name="event",
            name="start_time",
            field=models.TimeField(null=True),
        ),
    ]
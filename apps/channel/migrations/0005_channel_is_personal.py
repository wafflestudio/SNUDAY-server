# Generated by Django 3.1.6 on 2021-07-05 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0004_auto_20210228_1035"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="is_personal",
            field=models.BooleanField(default=False),
        ),
    ]
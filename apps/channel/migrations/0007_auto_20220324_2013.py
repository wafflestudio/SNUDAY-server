# Generated by Django 3.1.6 on 2022-03-24 11:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("channel", "0006_auto_20220313_0202"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="channel",
            name="managers",
        ),
        migrations.AddField(
            model_name="channel",
            name="managers",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="managing_channels",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

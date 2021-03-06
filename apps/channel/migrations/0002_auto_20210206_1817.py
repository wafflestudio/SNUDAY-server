# Generated by Django 3.1.6 on 2021-02-06 09:17

import apps.channel.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('channel', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=apps.channel.models.get_path)),
            ],
        ),
        migrations.AlterField(
            model_name='channel',
            name='image',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='channel.image'),
        ),
    ]

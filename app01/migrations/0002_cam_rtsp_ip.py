# Generated by Django 3.2.9 on 2021-11-25 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cam',
            name='rtsp_ip',
            field=models.URLField(default='10.10.211.93:8554/1'),
            preserve_default=False,
        ),
    ]

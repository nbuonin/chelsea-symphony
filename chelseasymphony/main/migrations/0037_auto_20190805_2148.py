# Generated by Django 2.2.4 on 2019-08-06 01:48

import chelseasymphony.main.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_auto_20190805_1335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concertdate',
            name='date',
            field=models.DateTimeField(default=chelseasymphony.main.models.default_concert_time),
        ),
    ]

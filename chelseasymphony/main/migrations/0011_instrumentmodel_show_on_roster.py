# Generated by Django 2.2.3 on 2019-07-20 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_auto_20190719_2308'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrumentmodel',
            name='show_on_roster',
            field=models.BooleanField(default=False),
        ),
    ]
# Generated by Django 2.1.2 on 2018-11-08 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_auto_20181107_1308'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='performer',
            options={'ordering': ['sort_order']},
        ),
        migrations.AddField(
            model_name='concertdate',
            name='sort_order',
            field=models.IntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='performer',
            name='sort_order',
            field=models.IntegerField(blank=True, editable=False, null=True),
        ),
    ]

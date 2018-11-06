# Generated by Django 2.1.2 on 2018-11-03 04:28

from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20181103_0359'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveRosterMusician',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('main.person',),
        ),
        migrations.AlterField(
            model_name='concertroster',
            name='performer',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, to='main.ActiveRosterMusician'),
        ),
    ]

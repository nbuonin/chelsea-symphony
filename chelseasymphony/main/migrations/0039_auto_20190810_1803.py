# Generated by Django 2.2.4 on 2019-08-10 22:03

from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0038_auto_20190810_1801'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='instrument',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, related_name='person_instrument', to='main.InstrumentModel'),
        ),
    ]

# Generated by Django 2.1.2 on 2018-11-03 03:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20181103_0134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concertroster',
            name='performer',
            field=models.ManyToManyField(related_name='_concertroster_performer_+', to='main.Person'),
        ),
    ]

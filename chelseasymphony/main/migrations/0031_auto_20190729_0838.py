# Generated by Django 2.2.3 on 2019-07-29 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0030_concertperformer'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='concertperformer',
            options={},
        ),
        migrations.AddConstraint(
            model_name='concertperformer',
            constraint=models.UniqueConstraint(fields=('concert', 'performer'), name='unique concert performer'),
        ),
    ]

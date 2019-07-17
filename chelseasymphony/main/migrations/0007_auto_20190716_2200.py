# Generated by Django 2.2.3 on 2019-07-17 02:00

from django.db import migrations, models
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_donate'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='legacy_id',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='concert',
            name='legacy_id',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='person',
            name='legacy_id',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='biography',
            field=wagtail.core.fields.RichTextField(blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='first_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]

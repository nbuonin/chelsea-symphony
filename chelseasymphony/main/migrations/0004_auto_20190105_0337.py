# Generated by Django 2.1.5 on 2019-01-05 03:37

from django.db import migrations
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20181213_0223'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='concertdate',
            name='sort_order',
        ),
        migrations.AddField(
            model_name='blogpost',
            name='promo_copy',
            field=wagtail.core.fields.RichTextField(default='Foobar'),
            preserve_default=False,
        ),
    ]

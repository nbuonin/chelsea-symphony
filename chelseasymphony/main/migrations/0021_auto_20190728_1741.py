# Generated by Django 2.2.3 on 2019-07-28 21:41

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_auto_20190728_1734'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='biography',
            field=wagtail.core.fields.StreamField([('paragraph', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.images.blocks.ImageChooserBlock())], blank=True),
        ),
    ]

# Generated by Django 2.2.4 on 2019-08-14 23:16

from django.db import migrations
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0039_auto_20190810_1803'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concert',
            name='venue',
            field=wagtail.core.fields.RichTextField(default="St. Paul'S Church, 315 West 22nd Street"),
        ),
    ]

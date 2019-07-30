# Generated by Django 2.2.3 on 2019-07-28 22:02

from django.db import migrations
from django.db import models, migrations
from wagtail.core.rich_text import RichText


def convert_to_streamfield(apps, schema_editor):
    FormPage = apps.get_model('main', 'FormPage')
    for page in FormPage.objects.all():
        if page.body.raw_text and not page.body:
            page.body = [('paragraph', RichText(page.body.raw_text))]
            page.save()

        if page.thank_you_text.raw_text and not page.thank_you_text:
            page.thank_you_text = [('paragraph', RichText(page.thank_you_text.raw_text))]
            page.save()


def convert_to_richtext(apps, schema_editor):
    FormPage = apps.get_model('main', 'FormPage')
    for page in FormPage.objects.all():
        if page.body.raw_text is None:
            raw_text = ''.join([
                child.value.source for child in page.body
                if child.block_type == 'paragraph'
            ])
            page.body = raw_text
            page.save()

        if page.thank_you_text.raw_text is None:
            raw_text = ''.join([
                child.value.source for child in page.thank_you_text
                if child.block_type == 'paragraph'
            ])
            page.thank_you_text = raw_text
            page.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_auto_20190728_1802'),
    ]

    operations = [
        migrations.RunPython(
            convert_to_streamfield,
            convert_to_richtext
        )
    ]
# Generated by Django 2.2.3 on 2019-07-21 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_person_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='basicpage',
            name='repeat_in_subnav',
            field=models.BooleanField(default=False, help_text="If checked, a link to this page will be repeated alongside it's direct children when displaying a sub-navigation for this page.", verbose_name='repeat in sub-navigation'),
        ),
        migrations.AddField(
            model_name='basicpage',
            name='repeated_item_text',
            field=models.CharField(blank=True, help_text="e.g. 'Section home' or 'Overview'. If left blank, the page title will be used.", max_length=255, verbose_name='repeated item link text'),
        ),
    ]

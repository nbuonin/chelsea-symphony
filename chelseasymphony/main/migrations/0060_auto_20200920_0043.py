# Generated by Django 3.1.1 on 2020-09-20 04:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0059_auto_20200919_2339'),
    ]

    operations = [
        migrations.AddField(
            model_name='personindex',
            name='repeat_in_subnav',
            field=models.BooleanField(default=False, help_text="If checked, a link to this page will be repeated alongside it's direct children when displaying a sub-navigation for this page.", verbose_name='repeat in sub-navigation'),
        ),
        migrations.AddField(
            model_name='personindex',
            name='repeated_item_text',
            field=models.CharField(blank=True, help_text="e.g. 'Section home' or 'Overview'. If left blank, the page title will be used.", max_length=255, verbose_name='repeated item link text'),
        ),
    ]

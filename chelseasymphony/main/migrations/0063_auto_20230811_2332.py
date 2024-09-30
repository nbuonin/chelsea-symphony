# Generated by Django 3.2.20 on 2023-08-12 03:32

from django.db import migrations, models
import django.db.models.deletion
import wagtail.core.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0023_add_choose_permissions'),
        ('main', '0062_concert_ticketing_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='home',
            name='supplimental_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='supplimental_image', to='wagtailimages.image'),
        ),
        migrations.AddField(
            model_name='home',
            name='supplimental_link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='home',
            name='supplimental_text',
            field=wagtail.core.fields.StreamField([('paragraph', wagtail.core.blocks.RichTextBlock()), ('button', wagtail.core.blocks.StructBlock([('button_text', wagtail.core.blocks.CharBlock(required=True)), ('button_link', wagtail.core.blocks.URLBlock(required=True))], template='main/blocks/button_block.html'))], blank=True),
        ),
        migrations.AddField(
            model_name='home',
            name='supplimental_title',
            field=models.CharField(blank=True, max_length=48, null=True),
        ),
    ]
# Generated by Django 2.2.4 on 2019-08-30 18:53

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0046_auto_20190828_0837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basicpage',
            name='body',
            field=wagtail.core.fields.StreamField([('paragraph', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.images.blocks.ImageChooserBlock()), ('block_quote', wagtail.core.blocks.StructBlock([('quote', wagtail.core.blocks.RichTextBlock(features=['italic'], required=True)), ('footer', wagtail.core.blocks.CharBlock()), ('alignment', wagtail.core.blocks.ChoiceBlock(choices=[('bc-left', 'Left'), ('bc-right', 'Right')]))], icon='openquote', template='main/blocks/block_quote.html')), ('highlight_link', wagtail.core.blocks.StructBlock([('heading', wagtail.core.blocks.CharBlock(required=True)), ('sub_heading', wagtail.core.blocks.CharBlock(required=True)), ('image', wagtail.images.blocks.ImageChooserBlock(required=True)), ('page', wagtail.core.blocks.PageChooserBlock(required=True))], icon='link', template='main/blocks/highlight_link.html')), ('personnel', wagtail.core.blocks.StructBlock([('left_caption', wagtail.core.blocks.CharBlock()), ('left_block', wagtail.core.blocks.ListBlock(wagtail.core.blocks.StructBlock([('role', wagtail.core.blocks.CharBlock()), ('people', wagtail.core.blocks.ListBlock(wagtail.core.blocks.StructBlock([('name', wagtail.core.blocks.CharBlock()), ('link', wagtail.core.blocks.URLBlock(required=False))])))]))), ('right_caption', wagtail.core.blocks.CharBlock()), ('right_block', wagtail.core.blocks.ListBlock(wagtail.core.blocks.StructBlock([('role', wagtail.core.blocks.CharBlock()), ('people', wagtail.core.blocks.ListBlock(wagtail.core.blocks.StructBlock([('name', wagtail.core.blocks.CharBlock()), ('link', wagtail.core.blocks.URLBlock(required=False))])))])))], icon='user', template='main/blocks/personnel.html'))]),
        ),
    ]

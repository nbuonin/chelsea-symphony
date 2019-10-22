# Generated by Django 2.2.4 on 2019-10-22 04:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtaildocs', '0010_document_file_hash'),
        ('main', '0050_auto_20190902_2311'),
    ]

    operations = [
        migrations.AddField(
            model_name='concert',
            name='program_notes',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='wagtaildocs.Document'),
        ),
    ]

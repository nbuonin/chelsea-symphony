# Generated by Django 2.2.3 on 2019-07-20 03:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_auto_20190719_1830'),
    ]

    operations = [
        migrations.AlterField(
            model_name='performance',
            name='conductor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.Person'),
        ),
    ]
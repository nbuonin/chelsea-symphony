# Generated by Django 2.2.3 on 2019-07-29 02:12

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_auto_20190728_2128'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConcertPerformer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('concert', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.PROTECT, related_name='performer', to='main.Concert')),
                ('performer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='main.Performer')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
    ]

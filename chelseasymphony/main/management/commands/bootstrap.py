from django.core.management.base import BaseCommand
from django.core.management import CommandError
from wagtail.core.models import Page
from chelseasymphony.main.tests.test_models import create_base_site
from chelseasymphony.main.models import InstrumentModel


class Command(BaseCommand):
    help = "Creates the index pages needed to start building out the site"

    def handle(self, *args, **kwargs):
        if Page.objects.count() > 2:
            raise CommandError('There already exists content in the database.')
        else:
            create_base_site()

            instrument_names = [
                'Violin',
                'Viola',
                'Cello',
                'Double Bass',
                'Harp',
                'Flute',
                'Oboe',
                'Clarinet',
                'Bassoon',
                'French Horn',
                'Trumpet',
                'Trombone',
                'Tuba',
                'Percussion',
                'Timpani',
                'Piano',
                'Harpsichord'
            ]
            for instrument in instrument_names:
                InstrumentModel.objects.create(
                    instrument=instrument
                )

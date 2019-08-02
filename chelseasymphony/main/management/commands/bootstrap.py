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
                ['Violin', True],
                ['Viola', True],
                ['Cello', True],
                ['Double Bass', True],
                ['Harp', True],
                ['Flute', True],
                ['Oboe', True],
                ['Clarinet', True],
                ['Bassoon', True],
                ['Horn', True],
                ['Trumpet', True],
                ['Trombone', True],
                ['Tuba', True],
                ['Percussion', True],
                ['Vibraphone', False],
                ['Timpani', True],
                ['Piano', True],
                ['Composer', False],
                ['Conductor', False],
                ['Harpsichord', False]
            ]
            for instrument, roster in instrument_names:
                InstrumentModel.objects.create(
                    instrument=instrument,
                    show_on_roster=roster
                )

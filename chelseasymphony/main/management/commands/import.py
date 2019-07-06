from django.core.management.base import BaseCommand
from dateutil.parser import isoparse
from pytz import timezone
import pytz

class Command(BaseCommand):
    help = 'Demo the command'

    def handle(self, *args, **kwargs):
        self.stdout.write('Yo Nick, it works')

        # example:
        # first parse the ISO to a datetime object, then localize it
        eastern = timezone('US/Eastern')

        d = isoparse('2019-06-29T20:00')
        new_date = eastern.localize(d)
        self.stdout.write(new_date.ctime())

from django.core.management.base import BaseCommand
from django.core.management import CommandError
from chelseasymphony.main.models import Person


class Command(BaseCommand):
    help = "This command deletes empty but instantiated StreamFields created by empty strings in the import data"

    def handle(self, *args, **kwargs):
        for p in Person.objects.all():
            # If the raw_text attr is empty, but the biography field is
            # instantiated, then delete the contents of the field
            if not p.biography.raw_text and p.biography:
                p.biography = []
                p.save_revision().publish()

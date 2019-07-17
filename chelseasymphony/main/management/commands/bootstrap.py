from django.core.management.base import BaseCommand
from django.core.management import CommandError
from wagtail.core.models import Page
from chelseasymphony.main.tests.test_models import create_base_site


class Command(BaseCommand):
    help = "Creates the index pages needed to start building out the site"

    def handle(self, *args, **kwargs):
        if Page.objects.count() > 2:
            raise CommandError('There already exists content in the database.')
        else:
            create_base_site()

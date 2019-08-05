"""Import biographies from Drupal site"""
import re
import requests
from django.core.management.base import BaseCommand
from django.utils.html import linebreaks
from wagtail.core.rich_text import RichText
from chelseasymphony.main.models import Person
IMPORT_BASE_URL = 'https://chelseasymphony.org'


class Command(BaseCommand):
    """Import biographies from Drupal site"""
    help = (
        "This command deletes empty but instantiated StreamFields created by"
        "empty strings in the import data"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = requests.get(IMPORT_BASE_URL + '/api/users').json()['nodes']
        self.people = [p['node'] for p in users]

    @staticmethod
    def escape_markup(text):
        """Replaces linebreaks with paragraph tags, removes new lines"""
        text = linebreaks(text, autoescape=True)
        text = re.sub(r'<br>', '</p><p>', text)
        return re.sub(r'\\n', '', text)

    def handle(self, *args, **kwargs):
        """Import User bios

        Look up person self.people from legacy id
        Get the bio text from the dict
        clean the text, as done in the import script
        Add it to the biography field
        Save revision and publish
        """
        for person in Person.objects.all():

            try:
                data = [prs for prs in self.people
                        if str(person.legacy_id) == prs['uid']][0]
            except IndexError:
                pass

            if data['biography']:
                clean_bio = self.escape_markup(data['biography'])
                person.biography = [('paragraph', RichText(clean_bio))]
                person.save_revision().publish()

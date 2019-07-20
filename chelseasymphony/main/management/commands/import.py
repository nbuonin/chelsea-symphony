from io import BytesIO
import os
from PIL import Image
import re
from urllib import parse
import requests
from chelseasymphony.main.models import (
    ConcertDate, ConcertIndex, Concert,
    Performance, Performer, Composition, Person, PersonIndex,
    InstrumentModel, BlogPost, BlogIndex
)
from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import make_aware
from wagtail.contrib.redirects.models import Redirect
from wagtail.core.rich_text import RichText
from wagtail.images import get_image_model

WagtailImage = get_image_model()
ContentType = apps.get_model('contenttypes.ContentType')


IMPORT_BASE_URL = 'http://localhost:8080'


class Command(BaseCommand):
    help = 'Demo the command'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.concert_idx = ConcertIndex.objects.first()
        except IndexError:
            print("The concert index does not exist")
            raise
        try:
            self.person_idx = PersonIndex.objects.first()
        except IndexError:
            print("The person index does not exist")
            raise
        try:
            self.blog_idx = BlogIndex.objects.first()
        except IndexError:
            print("The blog index does not exist")
            raise

    def fetch_data(self):
        # For concerts
        cns = requests.get(IMPORT_BASE_URL + '/api/concerts').json()['nodes']
        self.concerts = [c['node'] for c in cns]

        cdts = requests.get(
            IMPORT_BASE_URL + '/api/concert-date').json()['nodes']
        self.concert_dates = [d['node'] for d in cdts]

        cprf = requests.get(
            IMPORT_BASE_URL + '/api/performances').json()['nodes']
        self.concert_performances = [p['node'] for p in cprf]

        csls = requests.get(IMPORT_BASE_URL + '/api/soloists').json()['nodes']
        self.concert_soloists = [c['node'] for c in csls]

        cphts = requests.get(
            IMPORT_BASE_URL + '/api/concerts/images').json()['nodes']
        self.concert_photos = [p['node'] for p in cphts]

        users = requests.get(IMPORT_BASE_URL + '/api/users').json()['nodes']
        self.people = [p['node'] for p in users]

        hdshts = requests.get(
            IMPORT_BASE_URL + '/api/users/headshot').json()['nodes']
        self.headshots = [p['node'] for p in hdshts]

        bp = requests.get(IMPORT_BASE_URL + '/api/blogpost').json()['nodes']
        self.blog_posts = [b['node'] for b in bp]

        bp_img = requests.get(
            IMPORT_BASE_URL + '/api/blogpost-image').json()['nodes']
        self.blog_posts_images = [b['node'] for b in bp_img]

    def get_concert_dates(self, cid):
        """Gets concert dates by concert ID"""
        print('cid: ' + str(cid))
        return [d for d in self.concert_dates if d['nid'] == str(cid)][0]

    def get_concert_performances(self, nid):
        """Gets concert performances by concert ID"""
        performances = [p for p in self.concert_performances
                        if p['nid'] == str(nid)]
        return sorted(performances, key=lambda p: p['program_order'])

    def get_soloists_by_performance_id(self, nid):
        """Gets soloists by performance ID"""
        return [s for s in self.concert_soloists
                if s['performance_id'] == str(nid)]

    def get_concert_photo_by_id(self, nid):
        """
        Gets concert images by node id
        Note: this uses the tightest crop to set the focal point for the image
        """
        try:
            return [p for p in self.concert_photos
                    if (p['nid'] == str(nid) and
                        p['crop_style_name'] == 'tcs2r_concert_image_0_79')][0]
        except IndexError:
            return None

    def get_headshot_by_uid(self, uid):
        try:
            return [p for p in self.headshots
                    if (p['uid'] == str(uid) and
                        p['crop_style_name'] ==
                        'tcs2r_musician_headshot_1_5')][0]
        except IndexError:
            return None

    def get_blog_img_from_id(self, nid):
        try:
            return [p for p in self.blog_posts_images
                    if (p['nid'] == str(nid) and
                        p['crop_style_name'] ==
                        'tsc2r_blog_list___homepage_desktop')][0]
        except IndexError:
            return None

    def get_wagtail_image(self, url):
        """
        Looks for an existing image with the same name, otherwise downloads
        and saves the image.
        From: https://github.com/kevinhowbrook/wagtail-migration/blob/debdead7d5e9b3f00439e803642a3ef45ad2bb19/importers/base.py#L127
        """
        filename = self._filename_from_url(url)

        # see if an image with the same name exists
        try:
            return WagtailImage.objects.get(title=filename)
        except WagtailImage.DoesNotExist:
            pass

        # otherwise download
        print(f"Downloading {url}")
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error {response.status_code} downloading: {url}")
            return None

        # check its a valid image
        pil_image = Image.open(BytesIO(response.content))
        pil_image.verify()

        # save and return
        return WagtailImage.objects.create(
            title=filename,
            file=SimpleUploadedFile(filename, response.content)
        )

    def _filename_from_url(self, url):
        url_parsed = parse.urlparse(url)
        return os.path.split(url_parsed.path)[1]

    def get_or_create_person(self, name):
        name = name.strip()
        first = last = ''
        try:
            first, last = re.split(r'\s+', name, 1)
        except ValueError:
            last = name

        try:
            return Person.objects.get(first_name=first, last_name=last)
        except Person.MultipleObjectsReturned:
            # Names are ambigious! Because there are no pk's on composer names
            # from Drupal, just use the first Person we find
            return Person.objects.filter(
                first_name=first, last_name=last).first()
        except Person.DoesNotExist:
            person = Person(
                first_name=first,
                last_name=last,
                active_roster=False
            )
            self.person_idx.add_child(instance=person)
            person.save_revision().publish()
            return person

    def get_or_create_composition(self, composition, composer):
        try:
            return Composition.objects.get(title=composition)
        except Composition.DoesNotExist:
            cmpsr = self.get_or_create_person(composer) if composer else None
            return Composition.objects.create(
                title=composition,
                composer=cmpsr
            )

    def create_performances(self, concert):
        for perf in self.get_concert_performances(concert.legacy_id):
            print('Creating performance for concert ' + concert.title +
                  ': ' + perf['composition'])
            # This assumes that all Person objects are created first
            conductor = None
            if perf['conductor_uid']:
                conductor = Person.objects.get(legacy_id=perf['conductor_uid'])

            composition = self.get_or_create_composition(
                perf['composition'], perf['composer'])
            performance = Performance(
                conductor=conductor,
                composition=composition
            )
            concert.add_child(instance=performance)
            performance.save_revision().publish()

            for perf_date in re.split(r', ', perf['performance_date']):
                date = parse_date(perf_date)
                concert_date = concert.concert_date.get(date__date=date)
                performance.performance_date.add(concert_date)
                performance.save_revision().publish()

            for performer in self.\
                    get_soloists_by_performance_id(perf['performance_id']):
                print('Adding performer: ' + performer['soloist'])
                soloist = Person.objects.get(legacy_id=performer['uid'])
                instrument, created = InstrumentModel.objects.get_or_create(
                    instrument=performer['instrument'])
                Performer.objects.create(
                    performance=performance,
                    person=soloist,
                    instrument=instrument
                )

    def create_concert_dates(self, concert):
        dates = self.get_concert_dates(concert.legacy_id)
        date_strings = dates['concert_date'].split(', ')
        for d in date_strings:
            nieve_date = parse_datetime(d)
            aware_date = make_aware(nieve_date)
            c_date = ConcertDate.objects.create(
                concert=concert,
                date=aware_date
            )
            concert.concert_date.add(c_date)
            concert.save_revision().publish()

    def create_concert(self, c):
        venue = c['concert_location'] if c['concert_location'] \
            else "St. Paul's Church"

        concert = Concert(
            title=c['title'],
            promo_copy=c['promo_copy'],
            description=c['body'],
            venue=venue,
            legacy_id=c['nid']
        )
        concert.season = c['concert_season']
        self.concert_idx.add_child(instance=concert)
        concert.save_revision().publish()

        c_img = self.get_concert_photo_by_id(c['nid'])
        if c_img:
            concert_image = self.get_wagtail_image(
                c_img['concert_image']['src'])

            concert_image.focal_point_x = c_img['crop_area_X_offset']
            concert_image.focal_point_y = c_img['crop_area_Y_offset']
            concert_image.focal_point_width = c_img['crop_area_width']
            concert_image.focal_point_height = c_img['crop_area_height']
            concert.concert_image = concert_image
            concert.save()

        # Create a redirect
        Redirect.objects.create(old_path=c['path'], redirect_page=concert)
        return concert

    def create_concerts(self):
        if not self.concerts:
            self.fetch_data()

        concerts = (c for c in self.concerts
                    if not Concert.objects.filter(legacy_id=c['nid']).exists())
        for c in concerts:
            print('Creating concert: ' + c['title'])
            # Create the concert
            concert = self.create_concert(c)
            # Create dates for the concert
            self.create_concert_dates(concert)
            # Create performances
            self.create_performances(concert)

    def create_people(self):
        if not self.people:
            self.fetch_data()

        persons = (p for p in self.people
                   if not Person.objects.filter(legacy_id=p['uid']).exists())
        for p in persons:
            print('Now creating: ' + p['name'])
            active_roster = True if p['active_roster'] == "Yes" else False
            person = Person(
                first_name=p['first_name'],
                last_name=p['last_name'],
                biography=p['biography'],
                active_roster=active_roster,
                legacy_id=p['uid']
            )
            self.person_idx.add_child(instance=person)
            person.save_revision().publish()

            instrument, created = InstrumentModel.objects.\
                get_or_create(instrument=p['instrument'])
            person.instrument.add(instrument)
            person.save_revision().publish()

            h_img = self.get_headshot_by_uid(p['uid'])
            if h_img:
                headshot = self.get_wagtail_image(h_img['head_shot']['src'])
                headshot.focal_point_x = h_img['crop_area_X_offset']
                headshot.focal_point_y = h_img['crop_area_Y_offset']
                headshot.focal_point_width = h_img['crop_area_width']
                headshot.focal_point_height = h_img['crop_area_height']
                person.headshot = headshot
                person.save()

    def create_blogposts(self):
        if not self.blog_posts:
            self.fetch_data()

        posts = (p for p in self.blog_posts
                 if not BlogPost.objects.filter(legacy_id=p['nid']).exists())
        for post in posts:
            print('Creating blog post: ' + post['title'])
            # This assumes that all Persons will be created first
            author = Person.objects.get(legacy_id=post['author_uid'])
            blog_post = BlogPost(
                title=post['title'],
                legacy_id=post['nid'],
                promo_copy=post['promo_copy'],
                body=[('paragraph', RichText(post['body']))],
                author=author,
                date=parse_date(post['post_date'])
            )
            self.blog_idx.add_child(instance=blog_post)
            blog_post.save_revision().publish()

            # Create a redirect
            Redirect.objects.create(
                old_path=post['path'],
                redirect_page=blog_post)

            blog_img = self.get_blog_img_from_id(post['nid'])
            if blog_img:
                blog_image = self.get_wagtail_image(
                    blog_img['blog_image']['src'])
                blog_image.focal_point_x = blog_img['crop_area_X_offset']
                blog_image.focal_point_y = blog_img['crop_area_Y_offset']
                blog_image.focal_point_width = blog_img['crop_area_width']
                blog_image.focal_point_height = blog_img['crop_area_height']
                blog_post.blog_image = blog_image
                blog_post.save()

    def handle(self, *args, **kwargs):
        self.fetch_data()

        # Create people first, so that Concerts and Blogs can reference them
        self.create_people()

        # Then create concerts
        self.create_concerts()

        # Then create blog posts
        self.create_blogposts()

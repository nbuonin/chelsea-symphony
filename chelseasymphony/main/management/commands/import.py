from wagtail.core.models import Page, PageManager, Orderable, PageQuerySet, Site
from django.apps import apps
ContentType = apps.get_model('contenttypes.ContentType')
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import make_aware
from chelseasymphony.main.models import (
    Home, BasicPage, ConcertDate, ConcertIndex, Concert,
    Performance, Performer, Composition, Person, PersonIndex,
    InstrumentModel, BlogPost, BlogIndex, ActiveRosterMusician,
    Donate
)
from wagtail.core.rich_text import RichText
from wagtail.contrib.redirects.models import Redirect
from wagtail.images import get_image_model
WagtailImage = get_image_model()

from PIL import Image
import re


import requests

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

        cdts = requests.get(IMPORT_BASE_URL + '/api/concert-date').json()['nodes']
        self.concert_dates = [d['node'] for d in cdts]

        cprf = requests.get(IMPORT_BASE_URL + '/api/performances').json()['nodes']
        self.concert_performances = [p['node'] for p in cprf]

        csls = requests.get(IMPORT_BASE_URL + '/api/soloists').json()['nodes']
        self.concert_soloists = [c['node'] for c in csls]

        cphts = requests.get(IMPORT_BASE_URL + '/api/concerts/images').json()['nodes']
        self.concert_photos = [p['node'] for p in cphts]

        users = requests.get(IMPORT_BASE_URL + '/api/users').json()['nodes']
        self.people = [p['node'] for p in users]

        hdshts = requests.get(IMPORT_BASE_URL + '/api/users/headshot').json()['nodes']
        self.headshots = [p['node'] for p in hdshts]

        bp = requests.get(IMPORT_BASE_URL + '/api/blogpost').json()['nodes']
        self.blog_posts = [b['node'] for b in bp]

        bp_img = requests.get(IMPORT_BASE_URL + '/api/blogpost-image').json()['nodes']
        self.blog_posts_images = [b['node'] for b in bp]

    def get_concert_dates(self, id):
        """Gets concert dates by concert ID"""
        return [d for d in self.concert_dates if d['nid'] == id]

    def get_concert_performances(self, id):
        """Gets concert performances by concert ID"""
        performances = [p for p in self.concert_performances if p['nid'] == id]
        return sorted(performances, key=lambda p: p['program_order'])

    def get_soloists_by_performance_id(self, id):
        """Gets soloists by performance ID"""
        return [s for s in self.concert_soloists if s['performance_id'] == id]

    def get_concert_photo_by_id(self, nid):
        """
        Gets concert images by node id
        Note: this uses the tightest crop to set the focal point for the image
        """
        return [p for p in self.concert_photos
                if (p['nid'] == nid and
                    p['crop_style_name'] == 'tcs2r_concert_image_0_79')][0]

    def get_headshot_by_uid(self, uid):
        return [p for p in self.headshots
                if (p['uid'] == uid and
                    p['crop_style_name'] == 'tcs2r_musician_headshot_1_5')][0]

    def get_blog_img_from_id(self, nid):
        return [p for p in self.blog_posts_images
                if (p['nid'] == nid and
                    p['crop_style_name'] == 'tsc2r_blog_list___homepage_desktop')]

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
        except Person.DoesNotExist:
            person = Person(
                first_name=first,
                last_name=last
            )
            person.full_clean()
            self.person_idx.add_child(instance=person)
            person.save_revision.publish()
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
        """
        Get performances for a particular concert:
        "node" : {
            "title" : "RAGE + REMEMBRANCE",
            "nid" : "108",
            "composer" : "Aaron Israel Levin",
            "composition" : "In Between",
            "conductor" : "Matthew Aubin",
            "conductor_uid" : "12",
            "performance_id" : "363",
            "performance_date" : "2019-06-29, 2019-06-30",
            "program_order" : "0"
        }
        "node" : {
            "nid" : "108",
            "soloist" : "E.J. Lee",
            "uid" : "36",
            "instrument" : "Violin",
            "performance_id" : "366"
        }
        """
        for perf in this.get_concert_performances(concert.legacy_id):
            print('Creating performance for concert ' + concert.title +
                  ': ' + perf['composition'])
            # This assumes that all Person objects are created first
            conductor = Person.objects.get(legacy_id=perf['conductor_uid'])
            composition = self.get_or_create_composition(
                perf['composition'], perf['compose'])
            performance = Performance.objects.create(
                conductor=conductor,
                composition=composition
            )
            performance.full_clean()
            concert.add_child(instance=performance)
            performance.save_revision().publish()

            for perf_date in re.split(r', ', perf['performance_date']):
                date = parse_date(perf_date)
                concert_date = concert.concert_date.get(date__date=date)
                performance.performance_date.add(concert_date)

            for performer in self.\
                    get_soloists_by_performance_id(perf['performance_id']):
                print('Adding performer: ' + performer['soloist'])
                soloist = Person.objects.get(legacy_id=performer['uid'])
                instrument = InstrumentModel.objects.get_or_create(
                    instrument=performer['instrument]'])
                Performer.objects.create(
                    performance=performance,
                    person=soloist,
                    instrument=instrument
                )


    def create_concert_dates(self, concert):
        """
        "node" : {
            "title" : "RAGE + REMEMBRANCE",
            "concert_date" : "2019-06-29T20:00, 2019-06-30T14:00",
            "nid" : "108"
        }
        """
        dates = self.get_concert_dates(concert.legacy_id)
        date_strings = [d.strip() for d in dates['concert_date'].split(',')]
        for d in date_strings:
            nieve_date = parse_datetime(d)
            aware_date = make_aware(nieve_date)
            ConcertDate.objects.create(
                concert=concert,
                date=aware_date
            )

    def create_concert(self, c):
        """
        "node" : {
            "title" : "RAGE + REMEMBRANCE",
            "body" : "The Chelsea Symphony presents the season finale of RESOLUTION with a concert featuring John Corigliano's Symphony No. 1. Written in the late 1980s, the AIDS pandemic was claiming the lives of many. As the first of his large format works, the symphonic form here is used to commemorate, as the composer noted, \"my friends – those I had lost and the one I was losing.\" Partly inspired by the NAMES Project AIDS Memorial Quilt, the first movement is subtitled \"Apologue: Of Rage and Remembrance,\" and is dedicated to a pianist. The next two movements commemorate a music executive and a cellist. In the finale, a tarantella melody played by piano in a featured role and the cello line from the previous movements are juxtaposed against “a repeated pattern consisting of waves of brass chords ... [to convey] an image of timelessness.\"\n\nAlso on this finale series, TCS welcomes back two soloists to the stage for two solos for the violin: Adam von Housen performs the Mendelssohn's Violin Concerto in D minor on Saturday's concert, written by the prodigious composer when he was just 13 years old and forgotten until after his death. Sunday's matinee performance brings EJ Lee to the stage to close out our soloist season with the Beethoven Violin Concerto.\n\nBoth concerts open with In Between by Aaron Israel Levin, the winning composition from the 2018-19 TCS Composition Competition, now in its fifth year.\n\nTickets for reserved unassigned seating in a premium area are on sale at Eventbrite!\nTickets also available at the door for a suggested donation of $20. ",
            "Concert Image" : {
                "src" : "http://localhost:8080/sites/default/files/RageRemembranceBackground2.jpg",
                "alt" : "",
                "title" : ""
            },
            "concert_location" : "The DiMenna Center for Classical Music, 450 West 37th Street",
            "concert_season" : "2018-2019",
            "concert_tag" : "June 29-30",
            "nid" : "108",
            "path" : "/concert/rage-remembrance"
            }
        }
        """
        # Create the Concert Page
        venue = c['concert_location'] if c['concert_location'] \
            else "St. Paul's Church"
        redirect_path = c['path']

        c_img = self.get_concert_photo_by_id(c['nid'])
        concert_image = self.get_wagtail_image(
            c_img['concert_img']['src'])

        concert_image.focal_point_x = c_img['crop_area_X_offset']
        concert_image.focal_point_y = c_img['crop_area_Y_offset']
        concert_image.focal_point_width = c_img['crop_area_width']
        concert_image.focal_point_height = c_img['crop_area_height']

        concert = Concert(
            title=c['title'],
            promo_copy=c['promo_copy'],
            description=c['body'],
            concert_image=concert_image,
            venue=venue,
            legacy_id=c['nid']
        )
        concert.full_clean()
        self.concert_idx.add_child(instance=concert)
        concert.save_revision().publish()

        # Create a redirect
        Redirect.objects.create(old_path=c['path'], redirect_page=concert)
        return concert

    def create_concerts(self):
        if not self.concerts:
            self.fetch_data()

        concerts = (c for c in self.concerts
                    if not Concert.objects.exists(legacy_id=c['nid']))
        for c in concerts:
            print('Creating concert: ' + c['title'])
            # Create the concert
            concert = self.create_concert(c)
            # Create dates for the concert
            self.create_concert_dates(concert)
            # Create performances
            self.create_performances(concert)

    def create_people(self):
        """
        "node" : {
            "name" : "Aaron Dai",
            "uid" : "241",
            "first_name" : "Aaron",
            "last_name" : "Dai",
            "instrument" : "Piano",
            "biography" : "",
            "active" : "Yes",
            "active_roster" : "Yes"
        }
        """
        if not self.people:
            self.fetch_data()

        persons = (p for p in self.people
                  if not Person.objects.exists(legacy_id=p['uid']))
        for p in persons:
            print('Now creating: ' + p['name'])
            active_roster = True if p['active_roster'] == "Yes" else False
            person = Person(
                title=p['name'],
                first_name=p['first_name'],
                last_name=p['last_name'],
                biography=p['biography'],
                active_roster=active_roster,
                legacy_id=p['uid']
            )
            person.full_clean()
            self.person_idx.add_child(instance=person)
            person.save_revision().publish()

            instrument = InstrumentModel.objects.\
                get_or_create(instrument=p['instrument'])
            person.instrument.add(instrument)

            h_img = self.get_headshot_by_uid(p['uid'])
            if h_img:
                headshot = self.get_wagtail_image(headshot['head_shot']['src'])
                headshot.focal_point_x = h_img['crop_area_X_offset']
                headshot.focal_point_y = h_img['crop_area_Y_offset']
                headshot.focal_point_width = h_img['crop_area_width']
                headshot.focal_point_height = h_img['crop_area_height']
                person.headshot.add(headshot)


    def create_blogposts(self):
        if not self.blog_posts:
            self.fetch_data()

        posts = (p for p in self.blog_posts
                 if not BlogPost.objects.exists(legacy_id=p['nid']))
        for post in posts:
            print('Creating blog post: ' + post['title'])
            # This assumes that all Persons will be created first
            author = Person.objects.get(legacy_id=post['author_uid'])
            blog_post = BlogPost(
                title=post['title'],
                legacy_id=post['nid'],
                promo_copy=post['promo_copy'],
                body=[('rich_text', RichText(post['body']))],
                author=author,
                date=parse_date(post['post_date'])
            )
            blog_post.full_clean()
            self.blog_idx.add_child(instance=blog_post)
            blog_post.save_revision().publish()

            # Create a redirect
            Redirect.objects.create(
                old_path=post['path'],
                redirect_page=blog_post)

            blog_img = self.get_blog_img_from_id(post['nid'])
            if blog_img:
                blog_image = self.get_wagtail_image(blog_img['blog_image']['src'])
                blog_image.focal_point_x = post['crop_area_X_offset']
                blog_image.focal_point_y = post['crop_area_Y_offset']
                blog_image.focal_point_width = post['crop_area_width']
                blog_image.focal_point_height = post['crop_area_height']
                blog_post.blog_image.add(blog_image)

    def handle(self, *args, **kwargs):
        self.fetch_data()

        # Create people first, so that Concerts and Blogs can reference them
        self.create_people()

        # Then create concerts
        self.create_concerts()

        # Then create blog posts
        self.create_blogposts()


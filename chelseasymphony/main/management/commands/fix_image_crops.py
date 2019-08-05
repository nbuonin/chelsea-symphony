from io import BytesIO
import os
from urllib import parse
from math import floor
from PIL import Image
import requests
from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.images import get_image_model
from chelseasymphony.main.models import (
    Concert, Person, BlogPost
)

WagtailImage = get_image_model()
ContentType = apps.get_model('contenttypes.ContentType')


IMPORT_BASE_URL = 'https://chelseasymphony.org'


class Command(BaseCommand):
    """
    This class fixes broken image imports
    """
    help = (
        'This command fixes missing image crops. For this to work, the '
        'legacy must must have been previously imported.'
    )

    def __init__(self, *args, **kwargs):
        """Sets up instace variables"""
        super().__init__(*args, **kwargs)

        # For concerts
        cns = requests.get(IMPORT_BASE_URL + '/api/concerts').json()['nodes']
        self.concerts = [c['node'] for c in cns]

        cphts = requests.get(
            IMPORT_BASE_URL + '/api/concerts/images').json()['nodes']
        self.concert_photos = [p['node'] for p in cphts]

        users = requests.get(IMPORT_BASE_URL + '/api/users').json()['nodes']
        self.people = [p['node'] for p in users]

        hdshts = requests.get(
            IMPORT_BASE_URL + '/api/users/headshot').json()['nodes']
        self.headshots = [p['node'] for p in hdshts]

        blog_post = requests.get(
            IMPORT_BASE_URL + '/api/blogpost').json()['nodes']
        self.blog_posts = [b['node'] for b in blog_post]

        bp_img = requests.get(
            IMPORT_BASE_URL + '/api/blogpost-image').json()['nodes']
        self.blog_posts_images = [b['node'] for b in bp_img]

    def get_concert_photo_by_id(self, nid):
        """
        Gets concert images by node id
        Note: this uses the tightest crop to set the focal point for the image
        """
        try:
            return [p for p in self.concert_photos
                    if (p['nid'] == str(nid) and
                        p['crop_style_name'] == 'tcs2r_concert_image_2_7')][0]
        except IndexError:
            return None

    def get_headshot_by_uid(self, uid):
        """
        Gets a person's headshot based on thier legacy Drupal uid
        """
        try:
            return [p for p in self.headshots
                    if (p['uid'] == str(uid) and
                        p['crop_style_name'] ==
                        'tcs2r_concert_image_0_79')][0]
        except IndexError:
            pass

        try:
            return [p for p in self.headshots
                    if (p['uid'] == str(uid) and
                        p['crop_style_name'] == '')][0]
        except IndexError:
            return None

    def get_blog_img_from_id(self, nid):
        """
        Gets a blog image from legacy Drupal nid
        """
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
        From: https://github.com/kevinhowbrook/wagtail-migration/blob
              /debdead7d5e9b3f00439e803642a3ef45ad2bb19/importers/base.py#L127
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

    @staticmethod
    def _filename_from_url(url):
        # Get file name for image from a given URL
        url_parsed = parse.urlparse(url)
        return os.path.split(url_parsed.path)[1]

    def fix_concert_images(self):
        """Method to save missing crops on concert images"""
        concerts = (conc for conc in self.concerts
                    if Concert.objects.filter(legacy_id=conc['nid']).exists())
        for conc in concerts:
            # Create the concert
            concert = Concert.objects.get(legacy_id=conc['nid'])
            c_img = self.get_concert_photo_by_id(conc['nid'])
            if c_img:
                concert_image = self.get_wagtail_image(
                    c_img['concert_image']['src'])

                concert_image.focal_point_x = (
                    int(c_img['crop_area_X_offset']) +
                    floor(int(c_img['crop_area_width']) / 2)
                )
                concert_image.focal_point_y = (
                    int(c_img['crop_area_Y_offset']) +
                    floor(int(c_img['crop_area_height']) / 2)
                )
                concert_image.focal_point_width = int(
                    c_img['crop_area_width'])
                concert_image.focal_point_height = int(
                    c_img['crop_area_height'])
                concert_image.save()
                concert.concert_image = concert_image
                concert.save_revision().publish()

    def fix_people_headshots(self):
        """Adds missing crops to headshots"""
        persons = (p for p in self.people
                   if Person.objects.filter(legacy_id=p['uid']).exists())
        for pers in persons:
            print('Now creating: ' + pers['name'])
            person = Person.objects.get(legacy_id=pers['uid'])

            h_img = self.get_headshot_by_uid(pers['uid'])
            if h_img:
                headshot = self.get_wagtail_image(h_img['head_shot']['src'])
                if h_img['crop_style_name']:
                    print('{} has a crop'.format(pers['name']))
                    headshot.focal_point_x = (
                        int(h_img['crop_area_X_offset']) +
                        floor(int(h_img['crop_area_width']) / 2)
                    )
                    headshot.focal_point_y = (
                        int(h_img['crop_area_Y_offset']) +
                        floor(int(h_img['crop_area_height']) / 2)
                    )
                    headshot.focal_point_width = int(h_img['crop_area_width'])
                    headshot.focal_point_height = int(h_img['crop_area_height'])
                else:
                    print('{} does not have a crop'.format(pers['name']))
                    headshot.set_focal_point(
                        headshot.get_suggested_focal_point())

                headshot.save()
                person.headshot = headshot
                person.save_revision().publish()

    def fix_blogpost_img(self):
        """Adds missing crops to blog post images"""
        posts = (p for p in self.blog_posts
                 if BlogPost.objects.filter(legacy_id=p['nid']).exists())

        for post in posts:
            blog_post = BlogPost.objects.get(legacy_id=post['nid'])
            blog_img = self.get_blog_img_from_id(post['nid'])
            if blog_img:
                blog_image = self.get_wagtail_image(
                    blog_img['blog_image']['src'])
                blog_image.focal_point_x = (
                    int(blog_img['crop_area_X_offset']) +
                    floor(int(blog_img['crop_area_width']) / 2)
                )
                blog_image.focal_point_y = (
                    int(blog_img['crop_area_Y_offset']) +
                    floor(int(blog_img['crop_area_height']) / 2)
                )
                blog_image.focal_point_width = int(
                    blog_img['crop_area_width'])
                blog_image.focal_point_height = int(
                    blog_img['crop_area_height'])
                blog_image.save()
                blog_post.blog_image = blog_image
                blog_post.save_revision().publish()

    def handle(self, *args, **kwargs):
        # Create people first, so that Concerts and Blogs can reference them
        self.fix_people_headshots()

        # Then create concerts
        self.fix_concert_images()

        # Then create blog posts
        self.fix_blogpost_img()

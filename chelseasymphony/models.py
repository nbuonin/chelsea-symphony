from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.postgres.forms import RangeWidget

from modelcluster.fields import ParentalKey
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, \
    InlinePanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet


class Home(Page):
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='banner_image'
    )

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner_image')
    ]

    subpage_types = ['chelseasymphony.ConcertIndex']


class PerformanceDate(models.Model):
    concert = ParentalKey(
        'Concert',
        on_delete=models.CASCADE,
        related_name='performance_date'
    )
    date = models.DateTimeField()

    panels = [
        FieldPanel('date')
    ]


class Concert(Page):
    description = RichTextField()
    venue = RichTextField()
    #performances =
    concert_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='concert_image'
    )

    @property
    def conductors():
        pass

    content_panels = Page.content_panels + [
        FieldPanel('description'),
        FieldPanel('venue'),
        ImageChooserPanel('concert_image'),
        InlinePanel('performance_date', label="Performance Dates")
    ]

    parent_page_types = ['chelseasymphony.ConcertIndex']


class ConcertIndex(Page):
    parent_page_types = ['chelseasymphony.Home']
    subpage_types = ['chelseasymphony.Concert']


# @register_snippet
# class Performance(models.Model):
    # pass


# @register_snippet
# class Performer(models.Model):
    # pass


# @register_snippet
# class Composition(models.Model):
    # pass


# class Person(Page):
    # pass


# @register_snippet
# class Instrument(models.Model):
    # pass

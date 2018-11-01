from django import forms
from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.postgres.forms import RangeWidget

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core import blocks
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, \
    InlinePanel, StreamFieldPanel, PageChooserPanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet

from wagtailautocomplete.edit_handlers import AutocompletePanel

from modelcluster.models import ClusterableModel


class Home(Page):
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='banner_image'
    )

    def get_context(self, request):
        context = super().get_context(request)
        context['featured_concert'] = Concert.objects.all()[0]
        context['upcoming_concerts'] = Concert.objects.all()[1:3]
        context['recent_blog_posts'] = BlogPost.objects.all()[:2]

        return context

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner_image')
    ]

    subpage_types = [
        'ConcertIndex',
        'PersonIndex',
        'BlogIndex'
    ]


class SimplePage(Page):
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('body')
    ]


class PerformanceDate(models.Model):
    concert = ParentalKey(
        'Concert',
        on_delete=models.CASCADE,
        related_name='performance_date'
    )
    date = models.DateTimeField(
        null=False,
        blank=False
    )

    panels = [
        FieldPanel('date')
    ]


class ConcertIndex(Page):
    parent_page_types = ['Home']
    subpage_types = ['Concert']


class Concert(Page):
    description = RichTextField()
    venue = RichTextField()
    concert_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='concert_image'
    )

    @property
    def conductors():
        pass

    content_panels = Page.content_panels + [
        FieldPanel('description'),
        FieldPanel('venue'),
        ImageChooserPanel('concert_image'),
        InlinePanel('performance_date', label="Performance Dates"),
    ]

    parent_page_types = ['ConcertIndex']
    subpage_types = ['Performance']  # TODO add a roster page type


class Performance(Page):
    composition = models.ForeignKey(
        'Composition',
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name='+'
    )
    conductor = models.ForeignKey(
        'Person',
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name='+'
    )

    content_panels = Page.content_panels + [
        SnippetChooserPanel('composition'),
        InlinePanel('performer', label='Performers'),
        SnippetChooserPanel('conductor')
    ]

    parent_page_types = ['Concert']
    subpage_types = []


class Performer(models.Model):
    """
    This is a performer in the sense of an instance of a performance.
    """
    performance = ParentalKey(
        'Performance',
        on_delete=models.CASCADE,
        related_name='performer'
    )
    person = models.ForeignKey(
        'Person',
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name='+'
    )
    instrument = models.ForeignKey(
        'InstrumentModel',
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name='+'
    )

    content_panels = [
        PageChooserPanel('person'),
        SnippetChooserPanel('instrument')
    ]


@register_snippet
class Composition(models.Model):
    title = RichTextField()
    composer = models.ForeignKey(
        'Person',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    content_panels = [
        SnippetChooserPanel('composer')
    ]


class Person(Page):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    biography = RichTextField()
    active_roster= models.BooleanField()
    headshot = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+'
    )
    instrument = ParentalManyToManyField(
        'InstrumentModel',
        related_name='+'
    )

    content_panels = Page.content_panels + [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        FieldPanel('biography'),
        FieldPanel('active_roster'),
        ImageChooserPanel('headshot'),
        # # below may need to be a FieldPanel
        # SnippetChooserPanel('instrument')
    ]

    parent_page_types = ['PersonIndex']
    subpage_types = []


class PersonIndex(Page):
    # The roster page will go here
    parent_page_types = ['Home']
    subpage_types = ['Person']


@register_snippet
class InstrumentModel(models.Model):
    instrument = models.CharField(max_length=255)


class BlogPost(Page):
    author = models.ForeignKey(
        'Person',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    date = models.DateField()
    blog_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+'
    )
    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])

    content_panels = Page.content_panels + [
        FieldPanel('author'),
        FieldPanel('date'),
        ImageChooserPanel('blog_image'),
        StreamFieldPanel('body'),
    ]

    parent_page_types = ['BlogIndex']
    subpage_types = []


class BlogIndex(Page):
    parent_page_types = ['Home']
    subpage_types = ['BlogPost']

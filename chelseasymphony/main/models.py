from datetime import datetime
from html import unescape
from django import forms
from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.postgres.forms import RangeWidget
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.text import slugify
from django.utils.html import strip_tags, escape
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils.timezone import make_aware

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.core.models import Page, PageManager, Orderable, PageQuerySet
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core import blocks
from wagtail.core.url_routing import RouteResult
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, \
    InlinePanel, StreamFieldPanel, PageChooserPanel
from wagtail.admin.forms import WagtailAdminPageForm
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

    class Meta:
        verbose_name = "Homepage"

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

    class Meta:
        verbose_name = "Basic Page"

    def __str__(self):
        return self.title

    parent_page_types = [
        'Home',
        'ConcertIndex',
        'PersonIndex'
    ]


class ConcertDate(Orderable):
    concert = ParentalKey(
        'Concert',
        on_delete=models.CASCADE,
        related_name='concert_date'
    )
    date = models.DateTimeField(
        null=False,
        blank=False
    )

    class Meta:
        ordering = ['date']

    def __str__(self):
        return str(self.date)

    panels = [
        FieldPanel('date')
    ]


class ConcertIndex(Page):
    parent_page_types = ['Home']
    subpage_types = ['Concert']


class ConcertQuerySet(PageQuerySet):
    def concert_seasons(self):
        return self.values_list('season', flat=True)

    def future_concerts(self):
        concert_list = set()
        for date in ConcertDate.objects\
                .filter(date__gt=timezone.now()).select_related('concert'):
            concert_list.add(date.concert)

        return concert_list


ConcertManager = PageManager.from_queryset(ConcertQuerySet)

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
    roster = ParentalManyToManyField(
        'ActiveRosterMusician',
        blank=True
    )
    season = models.CharField(
        max_length=9,
        null=True
    )

    # TODO: needs tests
    @staticmethod
    def calculate_season(date):
        # The first day of the concert season is Aug 1
        season_first_day = make_aware(datetime(date.year, 8, 1))
        if date >= season_first_day:
            return "{}-{}".format(date.year, date.year + 1)
        else:
            return "{}-{}".format(date.year - 1, date.year)

    def _get_conductors(self):
        pass

    def _get_performances(self):
        pass

    def _get_program(self):
        pass

    def get_context(self, request):
        context = super().get_context(request)
        performances = self.get_descendants()\
            .select_related('performance__conductor')\
            .select_related('performance__composition')\
            .prefetch_related('performance_date')
        # TODO: query the conductors from child nodes
        context['conductors'] = None
        # Note that performances means something different from the class
        # Performance. It means a single concert and the performances that make
        # up a given day's concert.
        context['performances'] = None
        # A Program consists of: Composer's Name, Composition, Performers
        # Performers consist of name and instrument
        context['program'] = None

    def clean(self):
        super().clean()
        first_concert_date = self.concert_date.first().date
        self.season = self.calculate_season(first_concert_date)

    content_panels = Page.content_panels + [
        FieldPanel('description'),
        FieldPanel('venue'),
        ImageChooserPanel('concert_image'),
        InlinePanel('concert_date', label="Concert Dates"),
        FieldPanel('roster', widget=forms.CheckboxSelectMultiple)
    ]

    objects = ConcertManager()
    parent_page_types = ['ConcertIndex']
    subpage_types = ['Performance']


# TODO: write tests that verify that only parent dates make it into the child
# form
# TODO: write a test that verifies that 'default-slug' doesn't persist
class PerformanceAdminForm(WagtailAdminPageForm):
    def __init__(self, data=None, files=None, parent_page=None, *args, **kwargs):
        super().__init__(data, files, *args, **kwargs)
        # Set the dates from the parent page dates
        self.parent_page = parent_page
        self.fields['performance_date'].queryset = ConcertDate.objects\
            .filter(concert=parent_page.id)
        # Set a default value for the slug
        instance = kwargs.get('instance')
        if not instance.id:
            self.initial['slug'] = 'default-slug'


class Performance(Page):
    """
    A Performance page is a child of Concert pages.
    Its used to model performances of individual works within a Concert.
    These will publish as a list on the parent concert page.
    """
    base_form_class = PerformanceAdminForm
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
    performance_date = ParentalManyToManyField(
        'ConcertDate',
        blank=True
    )

    def clean(self):
        super().clean()
        self.title = str(self.composition)
        self.slug = slugify(self.title)

    # Route requests to these pages to their parent
    def get_url_parts(self, request=None):
        return self.get_parent().get_url_parts(request)

    content_panels = [
        SnippetChooserPanel('composition'),
        InlinePanel('performer', label='Performers'),
        PageChooserPanel('conductor'),
        FieldPanel(
            'performance_date',
            widget=forms.CheckboxSelectMultiple,
        )
    ]

    parent_page_types = ['Concert']
    subpage_types = []


class Performer(Orderable):
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
    # Note: calling unescape on the title below is only ok because the input is
    # being sanitized by the RichTextField.
    title = RichTextField(features=['bold', 'italic'])
    composer = models.ForeignKey(
        'Person',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    def __str__(self):
        return unescape(strip_tags(self.title))

    content_panels = [
        SnippetChooserPanel('composer')
    ]


# TODO: write a test that verifies that 'default-slug' doesn't persist
class PersonAdminForm(WagtailAdminPageForm):
    def __init__(self, data=None, files=None, parent_page=None, *args, **kwargs):
        super().__init__(data, files, *args, **kwargs)
        # Set a default value for the slug
        instance = kwargs.get('instance')
        if not instance.id:
            self.initial['slug'] = 'default-slug'


class Person(Page):
    base_form_class = PersonAdminForm
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

    def __str__(self):
        return "{} {}".format(
            self.first_name,
            self.last_name
        )

    def clean(self):
        super().clean()
        self.title = "{} {}".format(
            self.first_name,
            self.last_name
        )
        self.slug = slugify(self.title)

    content_panels = [
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
    def __str__(self):
        return self.instrument

    class Meta:
        verbose_name = "Instrument"


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


class ActiveRosterMusicianManager(PageManager):
    def get_queryset(self):
        return super().get_queryset().filter(active_roster=True)\
            .order_by('last_name')


class ActiveRosterMusician(Person):
    objects = ActiveRosterMusicianManager()
    class Meta:
        proxy = True

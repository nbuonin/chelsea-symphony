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
        context['upcoming_concerts'] = Concert.objects.all()[1:4]
        context['recent_blog_posts'] = BlogPost.objects.all()[:2]
        return context

    @classmethod
    def can_create_at(cls, parent):
        # Only one of these may be created
        return super().can_create_at(parent) and not cls.objects.exists()

    class Meta:
        verbose_name = "Homepage"

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner_image')
    ]

    parent_page_types = ['wagtailcore.Page']

    subpage_types = [
        'ConcertIndex',
        'PersonIndex',
        'BlogIndex',
        'BasicPage'
    ]


class BasicPage(Page):
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('body')
    ]

    class Meta:
        verbose_name = "Basic Page"

    def __str__(self):
        return self.title

    parent_page_types = ['Home']


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
    @classmethod
    def can_create_at(cls, parent):
        # Only one of these may be created
        return super().can_create_at(parent) and not cls.objects.exists()

    parent_page_types = ['Home']
    subpage_types = ['Concert']


class ConcertQuerySet(PageQuerySet):
    def concert_seasons(self):
        return self.values_list('season', flat=True)

    def future_concerts(self):
        return Concert.objects.\
            filter(concert_date__date__gt=timezone.now()).distinct()


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
        null=True,
        blank=True
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

    def get_context(self, request):
        context = super().get_context(request)
        performances = self.get_descendants().select_related(
                'performance__conductor',
                'performance__composition')

        # Conductors
        conductors = list()
        for p in performances:
            conductors.append({
                'name': p.specific.conductor.title,
                'url': p.specific.conductor.url
            })

        context['conductors'] = conductors

        # Program
        program = list()
        for p in performances:
            # First make a set of all performers for a given performance
            performers = list()
            for performer in p.specific.performer.all():
                performers.append({
                    'name': performer.person.title,
                    'url': performer.person.url,
                    'instrument': performer.instrument.instrument
                })

            # Then assemble with composer and composition
            program.append({
                'composer': p.specific.composition.composer.title,
                'composition': p.specific.composition.title,
                'performers': performers
            })
        context['program'] = program

        # Performer
        # This needs to display the performer, the work they are performing,
        # and the date they are performing it.
        performers = list()
        for p in performances:
            soloists = p.specific.performer.all()
            for s in soloists:
                performers.append({
                    'name': s.person.title,
                    'url': s.person.url,
                    'headshot': s.person.headshot,
                    'instrument': s.instrument.instrument,
                    'work': p.specific.composition.title,
                    'dates': [d.date for d in p.specific.performance_date.all()],
                    'bio': s.person.biography
                })

        context['performers'] = performers
        return context

    # TODO: needs test
    def performances_by_date(self):
        """
        Performances here means something different from the class
        Performance. It's a single concert and the performances that make
        up a given day's concert.

        This will be used on the Concert Index pages

        This method returns a dict that looks like:
            date
            program:
              * composer
              * composition
              * performers:
                * name
                * url
                * instrument
        """
        concert_dates = self.concert_date.all()
        performances_by_date = list()
        for cd in concert_dates:
            performances = list()
            ps = cd.performance_set.all()
            for p in ps:
                # First make a set of all performers for a given performance
                performers = list()
                for performer in p.specific.performer.all():
                    performers.append({
                        'name': performer.person.title,
                        'url': performer.person.url,
                        'instrument': performer.instrument.instrument
                    })

                # Then assemble with composer and composition
                performances.append({
                    'composer': p.specific.composition.composer.title,
                    'composition': p.specific.composition.title,
                    'performers': performers
                })

            # Finally assemble with the date
            performances_by_date.append({
                'date': cd.date,
                'program': performances
            })

        return performances_by_date

    def clean(self):
        super().clean()
        if self.concert_date.exists():
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

    # def save(self, commit=True):
        # page = super().save(commit=False)
        # page.title = "{} {}".format(
            # page.first_name,
            # page.last_name
        # )
        # page.slug = slugify(page.title)
        # if commit:
            # page.save()
        # return page


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
        related_name='person_instrument'
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
        # Can you check if a slug already exists?
        # when it raises a ValidationError where do catch that?
        # you might need to override save too
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

from datetime import datetime, date
from html import unescape
from django import forms
from django.db import models
from django.db.models import Max
from django.template.response import TemplateResponse
from django.utils.text import slugify
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.timezone import make_aware
from django.shortcuts import get_object_or_404

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.core.models import Page, PageManager, Orderable, PageQuerySet
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core import blocks
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
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

# For PayPal
from django.urls import reverse
from django.shortcuts import render
from paypal.standard.forms import PayPalPaymentsForm


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
        future_concerts = Concert.objects.future_concerts()
        context['featured_concert'] = future_concerts.first()
        context['upcoming_concerts'] = future_concerts[1:4]
        context['recent_blog_posts'] = BlogPost.objects.all()[:2]
        return context

    # TODO: you don't need this:
    # see
    # https://docs.wagtail.io/en/v2.5.1/reference/pages/model_reference.html#wagtail.core.models.Page.max_count
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
        'BasicPage',
        'Donate'
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


class ConcertDate(models.Model):
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


class ConcertIndex(RoutablePageMixin, Page):
    # TODO: pull this
    @classmethod
    def can_create_at(cls, parent):
        # Only one of these may be created
        return super().can_create_at(parent) and not cls.objects.exists()

    @route(r'^$')
    def upcoming_concerts(self, request):
        context = self.get_context(request)
        context['seasons'] = Concert.objects.concert_seasons()
        context['concerts'] = Concert.objects.future_concerts()
        return TemplateResponse(
            request,
            self.get_template(request),
            context
        )

    # TODO: You're injecting 'season' from the URL into the context.
    @route(r'(?P<season>\d{4}-\d{4})/$')
    def concerts_by_season(self, request, season):
        # Find the Season and raise 404 if it doesn't exist
        context = self.get_context(request)
        context['seasons'] = Concert.objects.concert_seasons()
        context['season'] = season
        context['concerts'] = Concert.objects.\
            annotate(last_date=Max('concert_date__date')).\
            filter(
                season=season,
                live=True,
                concert_date__date__isnull=False).distinct().\
            order_by('last_date')
        return TemplateResponse(
            request,
            self.get_template(request),
            context
        )

    @route(r'(?P<season>\d{4}-\d{4})/(?P<slug>[\w-]+)/?$')
    def get_concert(self, request, season, slug):
        concert_page = get_object_or_404(
            Concert,
            season=season,
            slug=slug
        )
        return concert_page.serve(request)

    parent_page_types = ['Home']
    subpage_types = ['Concert']


class ConcertQuerySet(PageQuerySet):
    def concert_seasons(self):
        return sorted(
            set(s for s in self.values_list('season', flat=True))
        )

    def future_concerts(self):
        today = timezone.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        return Concert.objects.\
            annotate(last_date=Max('concert_date__date')).\
            filter(
                last_date__gt=today,
                live=True,
                concert_date__date__isnull=False).distinct().\
            order_by('last_date')


ConcertManager = PageManager.from_queryset(ConcertQuerySet)


class Concert(Page):
    promo_copy = RichTextField(
        blank=True
    )
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
    legacy_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True
    )

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
                    'composer': p.specific.composition.composer.title,
                    'work': p.specific.composition.title,
                    'dates': [d.date for d in p.specific.performance_date.all()],
                    'bio': s.person.biography
                })

        context['performers'] = performers
        return context

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

    def set_url_path(self, parent):
        super().set_url_path(parent=parent)

        if self.concert_date.exists():
            first_concert_date = self.concert_date.first().date
            self.season = self.calculate_season(first_concert_date)
        elif not self.season:
            # The implicit logic here is that a concert object may have its
            # season set programatically from an import script. If its not set
            # then just use today's date to calculate the current season
            self.season = self.calculate_season(make_aware(datetime.now()))

        self.url_path = self.url_path.replace(
            self.slug,
            self.season + '/' + self.slug
        )

    def clean(self):
        # From Wagtail, done to make the tests go
        if not self.slug:
            # Try to auto-populate slug from title
            base_slug = slugify(self.title, allow_unicode=True)

            # only proceed if we get a non-empty base slug back from slugify
            if base_slug:
                self.slug = self._get_autogenerated_slug(base_slug)

        super().clean()

    content_panels = Page.content_panels + [
        FieldPanel('promo_copy'),
        FieldPanel('description'),
        FieldPanel('venue'),
        ImageChooserPanel('concert_image'),
        InlinePanel('concert_date', label="Concert Dates", min_num=1),
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
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+'
    )
    performance_date = ParentalManyToManyField(
        'ConcertDate',
        blank=True
    )

    def full_clean(self, *args, **kwargs):
        self.title = str(self.composition)
        super().full_clean(*args, **kwargs)

    def clean(self):
        self.title = str(self.composition)
        if not self.slug:
            # Try to auto-populate slug from title
            base_slug = slugify(self.title, allow_unicode=True)

            # only proceed if we get a non-empty base slug back from slugify
            if base_slug:
                self.slug = self._get_autogenerated_slug(base_slug)

        super().clean()

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
    first_name = models.CharField(
        blank=True,
        max_length=255
    )
    last_name = models.CharField(max_length=255)
    biography = RichTextField(
        blank=True,
    )
    active_roster = models.BooleanField()
    position = models.CharField(
        blank=True,
        max_length=255
    )
    headshot = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+'
    )
    instrument = ParentalManyToManyField(
        'InstrumentModel',
        related_name='person_instrument',
    )
    legacy_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True
    )

    def __str__(self):
        return "{} {}".format(
            self.first_name,
            self.last_name
        )

    def clean(self):
        self.title = "{} {}".format(
            self.first_name,
            self.last_name
        )
        # Lifted from Wagtail's full clean
        if not self.slug:
            # Try to auto-populate slug from title
            base_slug = slugify(self.title, allow_unicode=True)

            # only proceed if we get a non-empty base slug back from slugify
            if base_slug:
                self.slug = self._get_autogenerated_slug(base_slug)

        super().clean()

    def full_clean(self, *args, **kwargs):
        self.title = "{} {}".format(
            self.first_name,
            self.last_name
        )
        super().full_clean(*args, **kwargs)

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
    parent_page_types = ['Home']
    subpage_types = ['Person']

    def get_context(self, request):
        context = super().get_context(request)
        # For each instrument that is show on roster, get each musician that
        # is on the active roster
        roster = dict()
        instruments = InstrumentModel.objects.filter(show_on_roster=True)
        for i in instruments:
            musicians = Person.objects.filter(
                instrument__pk=i.pk, active_roster=True)\
                .order_by('last_name', 'first_name')
            roster[i.instrument] = [m for m in musicians]
        context['roster'] = roster
        return context


@register_snippet
class InstrumentModel(models.Model):
    instrument = models.CharField(max_length=255)
    show_on_roster = models.BooleanField(default=False)

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
    promo_copy = RichTextField(
        blank=True
    )
    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])
    legacy_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True
    )

    content_panels = Page.content_panels + [
        FieldPanel('author'),
        FieldPanel('date'),
        ImageChooserPanel('blog_image'),
        FieldPanel('promo_copy'),
        StreamFieldPanel('body'),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['recent_blog_posts'] = BlogPost.objects.live()\
            .order_by('-date')[:5]
        return context

    parent_page_types = ['BlogIndex']
    subpage_types = []


class BlogIndex(Page):
    parent_page_types = ['Home']
    subpage_types = ['BlogPost']

    def get_context(self, request):
        context = super().get_context(request)
        context['blog_posts'] = BlogPost.objects.live()\
            .order_by('-date')
        return context



class ActiveRosterMusicianManager(PageManager):
    def get_queryset(self):
        return super().get_queryset().filter(active_roster=True)\
            .order_by('last_name')


class ActiveRosterMusician(Person):
    objects = ActiveRosterMusicianManager()
    class Meta:
        proxy = True


class Donate(Page):
    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    def serve(self, request):
        single_donation_amounts = [
            '50.00',
            '100.00',
            '250.00',
            '500.00',
            '1000.00',
            '5000.00'
        ]

        recurring_donation_amounts = [
            '10.00',
            '15.00',
            '25.00',
            '50.00',
            '100.00',
            '125.00'
        ]

        paypal_dict_single = {
            "cmd": "_donations",
            "business": "info@chelseasymphony.org",
            "amount": "15.00",
            "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
            # "return": request.build_absolute_uri(reverse('your-return-view')),
            # "cancel_return": request.build_absolute_uri(reverse('your-cancel-view')),
        }

        paypal_dict_recurring = {
            "cmd": "_xclick-subscriptions",
            "business": "info@chelseasymphony.org",
            "src": "1",
            "srt": "24",
            "p3": "1",
            "t3": "M",
            "amount": "",
            "no_note": "1",
            "no_shipping": "2",
            "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
            # "return": request.build_absolute_uri(reverse('your-return-view')),
            # "cancel_return": request.build_absolute_uri(reverse('your-cancel-view')),
            # "custom": "premium_plan",  # Custom command to correlate to some function later (optional)
        }

        # Create the forms.
        form_single = PayPalPaymentsForm(initial=paypal_dict_single, button_type='donate')
        form_recurring = PayPalPaymentsForm(initial=paypal_dict_recurring, button_type='donate')
        context = {
            "page": self,
            "single": form_single,
            "recurring": form_recurring,
            "single_donation_amounts": single_donation_amounts,
            "recurring_donation_amounts": recurring_donation_amounts,
        }
        return render(request, "main/donate.html", context)

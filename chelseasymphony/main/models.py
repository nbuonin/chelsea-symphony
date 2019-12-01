"""Chelsea Symphony Models"""
from datetime import datetime, timedelta
from html import unescape
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Max, Min
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.text import slugify
from django.utils import timezone
from django.utils.html import strip_tags, format_html
from django.utils.timezone import make_aware, localtime
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.core.models import Page, PageManager, Orderable, PageQuerySet
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core import blocks
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.documents.models import Document
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.admin.edit_handlers import (
    FieldPanel, MultiFieldPanel, InlinePanel,
    StreamFieldPanel, PageChooserPanel, FieldRowPanel
)
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet
from wagtail.search import index
# For Menus
from wagtailmenus.models import MenuPageMixin
from wagtailmenus.panels import menupage_panel

from wagtailautocomplete.edit_handlers import AutocompletePanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.contrib.forms.edit_handlers import FormSubmissionsPanel

# For PayPal
from django.urls import reverse
from django.shortcuts import render
from paypal.standard.forms import PayPalPaymentsForm

# For Wagtail Metadata
from wagtailmetadata.models import MetadataPageMixin


class Home(MetadataPageMixin, Page):
    """Home Page Model"""
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='banner_image'
    )

    def get_context(self, request):
        context = super().get_context(request)
        future_concerts = Concert.objects.future_concerts().live().public()
        context['featured_concert'] = future_concerts.first()
        context['upcoming_concerts'] = future_concerts[1:4]
        context['recent_blog_posts'] = BlogPost.objects.all().\
            live().public().order_by('-date')[:2]
        return context

    max_count = 1

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
        'Donate',
        'FormPage',
        'NewMemberRequestPage',
    ]


class BasicPage(MetadataPageMixin, Page, MenuPageMixin):
    body = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('block_quote', blocks.StructBlock([
            ('quote', blocks.RichTextBlock(
                required=True,
                features=['italic'],
            )),
            ('footer', blocks.CharBlock()),
            ('alignment', blocks.ChoiceBlock(
                required=True,
                choices=[('bc-left', 'Left'), ('bc-right', 'Right')]
            ))
        ], template='main/blocks/block_quote.html', icon='openquote')),
        ('highlight_link', blocks.StructBlock([
            ('heading', blocks.CharBlock(required=True)),
            ('sub_heading', blocks.CharBlock(required=True)),
            ('image', ImageChooserBlock(required=True)),
            ('page', blocks.PageChooserBlock(required=True))
        ], template='main/blocks/highlight_link.html', icon='link')),
        ('personnel', blocks.StructBlock([
            ('left_caption', blocks.CharBlock()),
            ('left_block', blocks.ListBlock(
                blocks.StructBlock([
                    ('role', blocks.CharBlock()),
                    ('people', blocks.ListBlock(
                        blocks.StructBlock([
                            ('name', blocks.CharBlock()),
                            ('link', blocks.URLBlock(required=False))
                        ])
                    ))
                ])
            )),
            ('right_caption', blocks.CharBlock()),
            ('right_block', blocks.ListBlock(
                blocks.StructBlock([
                    ('role', blocks.CharBlock()),
                    ('people', blocks.ListBlock(
                        blocks.StructBlock([
                            ('name', blocks.CharBlock()),
                            ('link', blocks.URLBlock(required=False))
                        ])
                    ))
                ])
            )),
        ], template='main/blocks/personnel.html', icon='user'))
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body')
    ]

    settings_panels = Page.settings_panels + [
        menupage_panel
    ]

    class Meta:
        verbose_name = "Basic Page"

    def __str__(self):
        return self.title


def default_concert_time():
    start = datetime.now()
    start = start.replace(hour=20, minute=0, second=0, microsecond=0)
    start = make_aware(start)
    return start if start > timezone.now() else start + timedelta(days=1)


class ConcertDate(models.Model):
    concert = ParentalKey(
        'Concert',
        on_delete=models.CASCADE,
        related_name='concert_date'
    )
    date = models.DateTimeField(
        default=default_concert_time,
        null=False,
        blank=False
    )

    class Meta:
        ordering = ['date']

    def __str__(self):
        return localtime(self.date).strftime('%a, %b %d, %-I:%M %p')

    panels = [
        FieldPanel('date')
    ]


class ConcertIndex(RoutablePageMixin, Page):
    max_count = 1

    @route(r'^$')
    def upcoming_concerts(self, request):
        context = self.get_context(request)
        context['seasons'] = Concert.objects.concert_seasons()
        context['concerts'] = Concert.objects.future_concerts().live().public()
        context['previous_concerts'] = Concert.objects.\
            past_concerts_current_season().live().public()
        return TemplateResponse(
            request,
            self.get_template(request),
            context
        )

    @route(r'(?P<season>\d{4}-\d{4})/$')
    def concerts_by_season(self, request, season):
        seasons = Concert.objects.concert_seasons()
        if season not in seasons:
            raise Http404()

        context = self.get_context(request)
        context['seasons'] = seasons
        context['season'] = season
        context['concerts'] = Concert.objects.\
            annotate(last_date=Max('concert_date__date')).\
            filter(
                season=season,
                concert_date__date__isnull=False).distinct().\
            order_by('last_date').live().public()
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
        if not concert_page.live:
            raise Http404()

        if concert_page.get_view_restrictions():
            raise Http404()

        return concert_page.serve(request)

    @route(r'.+')
    def catch(self, request):
        """Catch any other routes that fall through and 404

        This is done so that concerts that share the same slug, but
        are members of different seasons, don't cause an error if
        a request is made to its default route.
        For example, /2018-2019/holiday/ and /2019-2020/holiday/
        are both routable under /holiday/
        This route catches those cases.
        """
        raise Http404

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
            annotate(first_date=Min('concert_date__date')).\
            annotate(last_date=Max('concert_date__date')).\
            filter(
                last_date__gt=today,
                live=True,
                concert_date__date__isnull=False).distinct().\
            order_by('first_date')

    def past_concerts_current_season(self):
        today = timezone.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        print(today)
        current_season = Concert.calculate_season(today)
        return Concert.objects.\
            annotate(first_date=Min('concert_date__date')).\
            annotate(last_date=Max('concert_date__date')).\
            filter(
                last_date__lte=today,
                season=current_season,
                live=True,
                concert_date__date__isnull=False).distinct().\
            order_by('first_date')


ConcertManager = PageManager.from_queryset(ConcertQuerySet)


class ConcertAdminForm(WagtailAdminPageForm):
    def __init__(
            self, data=None, files=None, parent_page=None, *args, **kwargs):
        super().__init__(data, files, *args, **kwargs)
        # Limit performer choices to those listed as performers in
        # child Performance pages
        instance = kwargs.get('instance')
        if instance.id:
            perfs = Performance.objects.live().descendant_of(self.instance)
            performers = Performer.objects.filter(performance__in=perfs)
            p_ids = [p.person.id for p in performers]
            people = Person.objects.filter(pk__in=p_ids)
            # Set the queryset for new Concert Performers
            self.formsets['performer'].form.\
                base_fields['person'].queryset = people
            # Set the queryset for existing Concert Performers
            for form in self.formsets['performer']:
                form.fields['person'].queryset = people

        else:
            self.formsets['performer'].form.\
                base_fields['person'].queryset = Person.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        # Check if a slug is available wrt the concert
        # season, and add an error if so
        if 'slug' in self.cleaned_data:
            first_concert_date = self.formsets['concert_date']\
                .cleaned_data[0]['date']
            season = self.instance.calculate_season(first_concert_date)
            qs = Concert.objects.filter(
                season=season, slug=self.cleaned_data['slug'])\
                .exclude(pk=self.instance.pk)
            if qs:
                self.add_error(
                    'slug',
                    forms.ValidationError(_("This slug is already in use")))

        return cleaned_data


class Concert(MetadataPageMixin, Page):
    base_form_class = ConcertAdminForm
    promo_copy = RichTextField(
        blank=True,
        features=['bold', 'italic'],
    )
    description = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('button', blocks.StructBlock([
            ('button_text', blocks.CharBlock(required=True)),
            ('button_link', blocks.URLBlock(required=True))
        ], template='main/blocks/button_block.html'))
    ])
    venue = RichTextField(
        default='St. Paul\'s Church, 315 West 22nd Street',
        features=['bold'],
    )
    concert_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='concert_image'
    )
    program_notes = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.PROTECT
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

    def get_meta_description(self):
        return self.search_description or self.promo_copy

    def get_meta_image(self):
        return self.search_image or self.concert_image

    def get_context(self, request):
        context = super().get_context(request)
        performances = self.get_descendants().live().public().select_related(
            'performance__conductor',
            'performance__composition')

        # Conductors
        # TODO: test that conductor exists, is live, and is public
        conductors = dict()
        for p in performances:
            conductor = p.specific.conductor
            if (conductor and conductor.is_live_public()):
                name = conductor.title
                conductors[name] = {
                    'name': name,
                    'last_name': p.specific.conductor.last_name,
                    'url': p.specific.conductor.url,
                    'headshot': p.specific.conductor.headshot,
                    'bio': p.specific.conductor.biography,
                }

        context['conductors'] = sorted(
            conductors.values(), key=lambda x: x['last_name'])

        # Program
        program = list()
        for p in performances:
            # First make a set of all performers for a given performance
            performers = list()
            # TODO: test that performer is live, is public()
            perfs = (p for p in p.specific.performer.all() if p.person.is_live_public())
            for performer in perfs:
                performers.append({
                    'name': performer.person.title,
                    'url': performer.person.url,
                    'instrument': performer.instrument.instrument
                })

            # Then assemble with composer and composition
            cmpsr = p.specific.composition.composer
            composer = None
            if cmpsr.is_live_public():
                composer = cmpsr

            program.append({
                'composer': composer.title if composer else 'Anon.',
                'composition': p.specific.composition.title,
                'supplemental_text': p.specific.supplemental_text,
                'performers': performers  # TODO: what happens if performers is null?
            })
        context['program'] = program

        # Performer
        # This needs to display the performer, the work they are performing,
        # and the date they are performing it.
        performers = list()
        for soloist in (p.person for p
                        in self.performer.all().order_by('sort_order')
                        if p.person.is_live_public()):
            # Select performances that have this soloist as a performer
            perfs = Performance.objects.descendant_of(self).\
                filter(performer__person__id=soloist.id).live().public()

            # Build up an aggregation of solo performances
            solo_perfs = list()
            solo_instrument = set()
            for p in perfs:
                cmpsr = p.composition.composer
                composer = None
                if cmpsr.is_live_public():
                    composer = cmpsr

                solo_perfs.append({
                    'composer': composer.title if composer else 'Anon.',
                    'work': p.composition.title,
                    'dates': [d.date for d in p.performance_date.all()]
                })
                s = p.performer.get(person__id=soloist.id)
                solo_instrument.add(s.instrument)

            performers.append({
                'name': soloist.title,
                'url': soloist.url,
                'headshot': soloist.headshot,
                'instrument': list(solo_instrument),
                'performances': solo_perfs,
                'bio': soloist.biography
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
            ps = cd.performance_set.all().live().public()
            for p in ps:
                # First make a set of all performers for a given performance
                performers = list()
                live_public_performers = (
                    perf for perf in p.specific.performer.all()
                    if perf.person.is_live_public())
                for performer in live_public_performers:
                    performers.append({
                        'name': performer.person.title,
                        'url': performer.person.url,
                        'instrument': performer.instrument.instrument
                    })

                # Then assemble with composer and composition
                cmpsr = p.specific.composition.composer
                composer = cmpsr if cmpsr.is_live_public() else 'Anon.'
                performances.append({
                    'composer': composer,
                    'composition': p.specific.composition.title,
                    'supplemental_text': p.specific.supplemental_text,
                    'performers': performers
                })

            # Finally assemble with the date
            performances_by_date.append({
                'date': cd.date,
                'program': performances
            })

        return performances_by_date

    def get_url_parts(self, *args, **kwargs):
        site_id, root_url, page_path = super().get_url_parts(*args, **kwargs)

        # Insert season in second to last position in path
        # Note: empty strings occupy the first and last positions
        # after spliting
        path = page_path.split('/')
        path.insert(-2, self.season)
        page_path = '/'.join(path)

        return (site_id, root_url, page_path)

    def full_clean(self, *args, **kwargs):
        if self.concert_date.exists():
            first_concert_date = self.concert_date.first().date
            self.season = self.calculate_season(first_concert_date)

        try:
            super().full_clean(*args, **kwargs)
        except ValidationError as err:
            # Only raise a validation error if concert slugs share the
            # same season
            if 'This slug is already in use' in err.messages:
                qs = Concert.objects.filter(
                    season=self.season, slug=self.slug).exclude(id=self.id)
                if qs:
                    raise err

    content_panels = Page.content_panels + [
        FieldPanel('promo_copy'),
        StreamFieldPanel('description'),
        FieldPanel('venue'),
        ImageChooserPanel('concert_image'),
        DocumentChooserPanel('program_notes'),
        InlinePanel('concert_date', label="Concert Dates", min_num=1),
        InlinePanel(
            'performer',
            label='Concert Performers',
            help_text=(
                'Performers listed on the concert can be managed here. '
                'Create some performances to populate the drop down '
                'menus with names.'
            )
        ),
        # Save for future use
        # FieldPanel('roster', widget=forms.CheckboxSelectMultiple)
    ]

    promote_panels = [
        MultiFieldPanel([
            FieldPanel('slug'),
            FieldPanel('seo_title'),
            FieldPanel('show_in_menus'),
            FieldPanel(
                'search_description',
                help_text=(
                    'Use this field for short descriptions on social media '
                    'sites. Otherwise the promo text will be used.')),
            ImageChooserPanel('search_image'),
        ], ugettext_lazy('Common page configuration')),
    ]

    objects = ConcertManager()
    parent_page_types = ['ConcertIndex']
    subpage_types = ['Performance']


# TODO: write tests that verify that only parent dates make it into the child
# form
class PerformanceAdminForm(WagtailAdminPageForm):
    def __init__(
            self, data=None, files=None, parent_page=None, *args, **kwargs):
        super().__init__(data, files, *args, **kwargs)
        # Set the dates from the parent page dates
        self.parent_page = parent_page
        self.fields['performance_date'].queryset = ConcertDate.objects\
            .filter(concert=parent_page.id)


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
    supplemental_text = RichTextField(
        blank=True,
        features=['bold', 'italic']
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
        # Clear sluge and let Wagtail resolve it
        self.slug = ''
        super().full_clean(*args, **kwargs)

    def clean(self):
        self.title = str(self.composition)
        super().clean()

    # Route requests to these pages to their parent
    def get_url_parts(self, *args, **kwargs):
        return self.get_parent().specific.get_url_parts(*args, **kwargs)

    content_panels = [
        AutocompletePanel(
            'composition',
            target_model='main.Composition'
        ),
        FieldPanel('supplemental_text'),
        InlinePanel('performer', label='Performers'),
        AutocompletePanel(
            'conductor',
            target_model='main.Person'
        ),
        FieldPanel(
            'performance_date',
            widget=forms.CheckboxSelectMultiple,
        )
    ]

    promote_panels = []

    parent_page_types = ['Concert']
    subpage_types = []


class ConcertPerformer(Orderable):
    """
    This is another representation of a performer, but for ordering
    on a per concert basis
    """
    concert = ParentalKey(
        'Concert',
        on_delete=models.CASCADE,
        related_name='performer',
    )
    person = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='+',
    )

    def is_performer_live_public(self):
        return self.person.live and not self.person.get_view_restrictions()

    def get_performer(self):
        if (self.person.live and not self.person.get_view_restrictions()):
            return self.person

        return None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['concert', 'person'],
                name='unique concert performer'
            )
        ]


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

    def is_performer_live_public(self):
        return self.person.live and not self.person.get_view_restrictions()

    def get_performer(self):
        if (self.person.live and not self.person.get_view_restrictions()):
            return self.person

        return None


    def __str__(self):
        return "{} - {}".format(
            self.person.title,
            self.instrument,
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # If not saved as a concert performer already, then
        # create a concert performer
        concert = self.performance.get_parent().specific
        if not ConcertPerformer.objects.filter(
                concert__pk=concert.id, person=self.person).exists():
            ConcertPerformer.objects.create(
                concert=concert,
                person=self.person
            )

    def delete(self, *args, **kwargs):
        # Before deleting, check if other siblings list this person as a
        # performer, if so, than delete this particular performer, but leave
        # the concert performer alone.
        # If not, then delete the concert performer first, then delete
        concert = self.performance.get_parent().specific
        sibling_perfs = [
            p.specific for p in self.performance.get_siblings(inclusive=False)]

        found = False
        for perf in sibling_perfs:
            for person in perf.performer.all():
                if person.id == self.person.id:
                    found = True
                    break

        if not found:
            try:
                ConcertPerformer.objects.get(
                    concert__pk=concert.id, person=self.person
                ).delete()
            except ConcertPerformer.DoesNotExist:
                pass

        super().delete(*args, **kwargs)

    panels = [
        AutocompletePanel('person', target_model='main.Person'),
        AutocompletePanel('instrument', target_model='main.InstrumentModel'),
    ]


@register_snippet
class Composition(index.Indexed, models.Model):
    # Note: calling unescape on the title below is only ok because the input is
    # being sanitized by the RichTextField.
    title = RichTextField(features=['bold', 'italic'])
    composer = models.ForeignKey(
        'Person',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    def __str__(self):
        return unescape(strip_tags(self.title))

    def display_title(self):
        return str(self)

    def autocomplete_label(self):
        return "{} - {}".format(
            unescape(strip_tags(self.title)),
            self.composer
        )

    panels = [
        FieldPanel('title'),
        AutocompletePanel(
            'composer',
            target_model='main.Person')
    ]

    search_fields = [
        index.SearchField('title', partial_match=True),
        index.RelatedFields('composer', [
            index.SearchField('first_name', partial_match=True),
            index.SearchField('last_name', partial_match=True),
        ]),
    ]


class Person(MetadataPageMixin, Page):
    # base_form_class = PersonAdminForm
    first_name = models.CharField(
        blank=True,
        max_length=255
    )
    last_name = models.CharField(max_length=255)
    biography = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ], blank=True)

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
        blank=True,
    )
    legacy_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True
    )

    def is_live_public(self):
        return self.live and not self.get_view_restrictions()

    def get_meta_image(self):
        return self.search_image or self.headshot

    def __str__(self):
        return "{} {}".format(
            self.first_name,
            self.last_name
        )

    def clean(self):
        self.title = self.__str__()
        super().clean()

    def full_clean(self, *args, **kwargs):
        self.title = self.__str__()
        # Clear the slug and let Wagtail resolve it
        self.slug = ''
        super().full_clean(*args, **kwargs)

    content_panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        StreamFieldPanel('biography'),
        FieldPanel('active_roster'),
        ImageChooserPanel('headshot'),
        FieldPanel(
            'instrument',
            widget=forms.CheckboxSelectMultiple
        )
    ]

    promote_panels = [
        MultiFieldPanel([
            FieldPanel('seo_title'),
            FieldPanel('show_in_menus'),
            FieldPanel('search_description'),
            ImageChooserPanel(
                'search_image',
                help_text=(
                    'Select an image to be used for social media sites. '
                    'Otherwise, the headshot image will be used.')),
        ], ugettext_lazy('Common page configuration')),
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
        instruments = InstrumentModel.objects\
            .filter(show_on_roster=True).order_by('weight')
        for i in instruments:
            musicians = Person.objects.filter(
                instrument__pk=i.pk, active_roster=True)\
                .live().public().order_by('last_name', 'first_name')
            roster[i.instrument] = [m for m in musicians]
        context['roster'] = roster
        return context


@register_snippet
class InstrumentModel(models.Model):
    instrument = models.CharField(max_length=255)
    show_on_roster = models.BooleanField(default=False)
    weight = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        unique=True
    )

    autocomplete_search_field = 'instrument'

    def autocomplete_label(self):
        return str(self)

    def __str__(self):
        return self.instrument

    class Meta:
        verbose_name = "Instrument"


class BlogPost(MetadataPageMixin, Page):
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
        blank=True,
        features=['bold', 'italic'],
    )
    body = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])
    legacy_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True
    )

    content_panels = Page.content_panels + [
        AutocompletePanel('author', target_model='main.Person'),
        FieldPanel('date'),
        ImageChooserPanel('blog_image'),
        FieldPanel('promo_copy'),
        StreamFieldPanel('body'),
    ]

    promote_panels = [
        MultiFieldPanel([
            FieldPanel('slug'),
            FieldPanel('seo_title'),
            FieldPanel('show_in_menus'),
            FieldPanel(
                'search_description',
                help_text=('Description to be used for social media sites. '
                           'Otherwise, the promo text will be used.')),
            ImageChooserPanel(
                'search_image',
                help_text=('Image to be used for social media sites. '
                           'Otherwise, the blog image will be used.')),
        ], ugettext_lazy('Common page configuration')),
    ]

    def get_meta_description(self):
        return self.search_description or self.promo_copy

    def get_meta_image(self):
        return self.search_image or self.blog_image

    def get_context(self, request):
        context = super().get_context(request)
        context['recent_blog_posts'] = BlogPost.objects.live().public()\
            .order_by('-date')[:5]
        return context

    parent_page_types = ['BlogIndex']
    subpage_types = []


class BlogIndex(Page):
    parent_page_types = ['Home']
    subpage_types = ['BlogPost']

    def get_context(self, request):
        context = super().get_context(request)
        context['blog_posts'] = BlogPost.objects.live().public()\
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


class Donate(RoutablePageMixin, Page):
    body = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])

    thank_you_text = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ], blank=True)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
        StreamFieldPanel('thank_you_text'),
    ]

    @route(r'thank-you/$')
    def thank_you(self, request):
        context = self.get_context(request)
        return render(request, "main/donate_thank_you.html", context)

    @route(r'^$')
    def donation_form(self, request):
        context = self.get_context(request)
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
            "business": settings.PAYPAL_ACCT_EMAIL,
            "amount": "",
            "no_note": "1",
            "no_shipping": "2",
            "item_name": "Single donation for The Chelsea Symphony",
            "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
            "return": self.full_url + 'thank-you/',
            "cancel_return": self.full_url,
            "custom": "",
            "rm": "1"
        }

        paypal_dict_recurring = {
            "cmd": "_xclick-subscriptions",
            "business": settings.PAYPAL_ACCT_EMAIL,
            "src": "1",
            "srt": "24",
            "p3": "1",
            "t3": "M",
            "no_note": "1",
            "no_shipping": "2",
            "a3": "",
            "item_name": "Recurring donation for The Chelsea Symphony",
            "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
            "return": self.full_url + 'thank-you/',
            "cancel_return": self.full_url,
            "custom": "",
            "rm": "1"
        }

        form_single = PayPalPaymentsForm(
            initial=paypal_dict_single,
            button_type='donate')
        form_recurring = PayPalPaymentsForm(
            initial=paypal_dict_recurring,
            button_type='donate')
        context = {
            "page": self,
            "single": form_single,
            "recurring": form_recurring,
            "single_donation_amounts": single_donation_amounts,
            "recurring_donation_amounts": recurring_donation_amounts,
        }
        return render(request, "main/donate.html", context)


class FormField(AbstractFormField):
    page = ParentalKey('FormPage',
                       on_delete=models.CASCADE,
                       related_name='form_fields')


class FormPage(AbstractEmailForm, MenuPageMixin):
    body = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ], blank=True)
    thank_you_text = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ], blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        StreamFieldPanel('body', classname='full'),
        StreamFieldPanel('thank_you_text', classname='full'),
        InlinePanel('form_fields', label="Form fields"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]

    settings_panels = AbstractEmailForm.settings_panels + [
        menupage_panel,
    ]


class NewMemberRequest(models.Model):
    VIOLIN = 'violin'
    VIOLA = 'viola'
    CELLO = 'cello'
    BASS = 'bass'
    HARP = 'harp'
    FLUTE = 'flute'
    OBOE = 'oboe'
    CLARINET = 'clarinet'
    BASSOON = 'bassoon'
    HORN = 'horn'
    TRUMPET = 'trumpet'
    TROMBONE = 'trombone'
    TUBA = 'tuba'
    PERCUSSION = 'percussion'
    PIANO = 'piano'
    INSTRUMENT_CHOICES = [
        (VIOLIN, 'Violin'),
        (VIOLA, 'Viola'),
        (CELLO, 'Cello'),
        (BASS, 'Bass'),
        (HARP, 'Harp'),
        (FLUTE, 'Flute'),
        (OBOE, 'Oboe'),
        (CLARINET, 'Clarinet'),
        (BASSOON, 'Bassoon'),
        (HORN, 'Horn'),
        (TRUMPET, 'Trumpet'),
        (TROMBONE, 'Trombone'),
        (TUBA, 'Tuba'),
        (PERCUSSION, 'Percussion'),
        (PIANO, 'Piano'),
    ]

    PERFORMANCE = 'performance'
    MUSICIAN = 'musician'
    SEARCH = 'search'
    MITJ = 'mozart_in_the_jungle'
    OTHER = 'other'
    SOURCE_CHOICES = [
        (PERFORMANCE, 'Attended a performance'),
        (MUSICIAN, 'From a TCS musician'),
        (SEARCH, 'Internet search'),
        (MITJ, 'Mozart in the Jungle'),
        (OTHER, 'Other'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)
    email = models.EmailField()
    instrument = models.CharField(
        max_length=254,
        choices=INSTRUMENT_CHOICES,
    )
    resume = models.FileField(
        upload_to='resumes/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'txt'])
        ]
    )
    source = models.CharField(
        max_length=254,
        choices=SOURCE_CHOICES
    )
    link = models.URLField(blank=True)
    read_policies = models.BooleanField()


class NewMemberRequestPage(MetadataPageMixin, Page, MenuPageMixin):
    body = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])

    thank_you_text = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
        StreamFieldPanel('thank_you_text')
    ]

    settings_panels = Page.settings_panels + [
        menupage_panel
    ]

    def serve(self, request):
        from .forms import NewMemberRequestForm
        if request.method == 'POST':
            form = NewMemberRequestForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return render(request, 'main/form_page_landing.html', {
                    'page': self,
                })

        else:
            form = NewMemberRequestForm()

        return render(request, 'main/form_page.html', {
            'page': self,
            'form': form
        })

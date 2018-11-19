from datetime import (
    datetime, timedelta
)
from django.utils.timezone import get_current_timezone
from faker import Factory
from factory import (
    DjangoModelFactory, SubFactory, post_generation, RelatedFactory,
    LazyAttribute
)
from wagtail_factories import (
    PageFactory, ImageChooserBlockFactory
)
from chelseasymphony.main.models import (
    Home, BasicPage, ConcertDate, ConcertIndex, Concert,
    Performance, Performer, Composition, Person, PersonIndex,
    InstrumentModel, BlogPost, BlogIndex, ActiveRosterMusician
)

INSTRUMENT_NAMES = [
    'Violin',
    'Viola',
    'Cello',
    'Double Bass',
    'Harp',
    'Flute',
    'Oboe',
    'Clarinet',
    'Bassoon',
    'French Horn',
    'Trumpet',
    'Trombone',
    'Tuba',
    'Percussion',
    'Timpani',
    'Piano',
    'Harpsichord'
]

faker = Factory.create()


class CompositionFactory(DjangoModelFactory):
    title = None
    # Many-to-one to Person
    Composer = None


class PerformanceFactory(PageFactory):
    composition = None
    conductor = None
    performance_date = None
    # MtM to performer

    class Meta:
        model = Performance


class ConcertDateFactory(DjangoModelFactory):
    concert = None
    d = faker.future_date(end_date="+1y")
    date = datetime(
        year=d.year, month=d.month, day=d.day, hour=20)

    class Meta:
        model = ConcertDate
        exclude = ('d',)


class ConcertFactory(PageFactory):
    description = faker.text(max_nb_chars=200, ext_word_list=None)
    venue = faker.text(max_nb_chars=200, ext_word_list=None)
    concert_image = SubFactory(ImageChooserBlockFactory)

    @post_generation
    def make_concert_dates(self, create, extracted, **kwargs):
        if not create:
            return
        else:
            future = kwargs.get('future', True)
            tz = get_current_timezone()
            if future:
                d = faker.date_between(start_date="-1y", end_date="-2d")
                concert_1 = datetime(
                    year=d.year, month=d.month, day=d.day, hour=20, tzinfo=tz)
                day = timedelta(days=+1)
                concert_2 = concert_1 + day
                ConcertDateFactory(concert=self, date=concert_1)
                ConcertDateFactory(concert=self, date=concert_2)
            else:
                d = faker.future_date(end_date="+1y")
                concert_1 = datetime(
                    year=d.year, month=d.month, day=d.day, hour=20, tzinfo=tz)
                day = timedelta(days=+1)
                concert_2 = concert_1 + day
                ConcertDateFactory(concert=self, date=concert_1)
                ConcertDateFactory(concert=self, date=concert_2)

    @post_generation
    def roster(self, create, extracted, **kwargs):
        if create:
            # Check if People exist, if not make some, else asign some
            if ActiveRosterMusician.objects.exists():
                self.roster.add(
                    ActiveRosterMusician.objects.order_by('?').first()
                )
            else:
                for p in range(25):
                    PersonFactory()

                self.roster.add(
                    ActiveRosterMusician.objects.order_by('?').first()
                )
        else:
            return
        if extracted:
            for i in extracted:
                self.roster.add(i)

    # Create four performances for each concert
    # RelatedFactory(PerformanceFactory)
    # RelatedFactory(PerformanceFactory)
    # RelatedFactory(PerformanceFactory)
    # RelatedFactory(PerformanceFactory)

    class Meta:
        model = Concert

class InstrumentModelFactory(DjangoModelFactory):
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        If instruments already exist, pick a random one and return.
        If they don't exist, generate them from the list of names, and return it
        Otherwise, if called with kwargs, behave as expected.
        """
        inst = kwargs.get('instrument', None)
        if inst:
            # get or create
            if InstrumentModel.objects.exists():
                return InstrumentModel.objects.get_or_create(instrument=inst)
            else:
                for i in INSTRUMENT_NAMES:
                    InstrumentModel.objects.create(*args, instrument=i)

                return InstrumentModel.objects.order_by('?').first()
        else:
            return super()._create(model_class, *args, **kwargs)

    class Meta:
        model = InstrumentModel


class PersonFactory(PageFactory):
    first_name = faker.first_name()
    last_name = faker.last_name()
    biography = faker.text(max_nb_chars=200, ext_word_list=None)
    active_roster = True
    headshot = SubFactory(ImageChooserBlockFactory)
    instrument = RelatedFactory(InstrumentModelFactory)

    # @classmethod
    # def _create(cls, model_class, *args, **kwargs):
        # if not kwargs:
            # if Person.objects.exist

    class Meta:
        model = Person

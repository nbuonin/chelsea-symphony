from datetime import (
    datetime, timedelta
)
from django.utils.timezone import get_current_timezone
from django.utils.text import slugify
from factory import (
    DjangoModelFactory, SubFactory, post_generation, RelatedFactory,
    LazyAttribute, Faker
)
from wagtail_factories import (
    PageFactory, ImageChooserBlockFactory
)
from chelseasymphony.main.models import (
    Home, BasicPage, ConcertDate, ConcertIndex, Concert,
    Performance, Performer, Composition, Person, PersonIndex,
    InstrumentModel, BlogPost, BlogIndex, ActiveRosterMusician
)

TZ = get_current_timezone()

INSTRUMENT_NAMES = [
    ['Violin', True],
    ['Viola', True],
    ['Cello', True],
    ['Double Bass', True],
    ['Harp', True],
    ['Flute', True],
    ['Oboe', True],
    ['Clarinet', True],
    ['Bassoon', True],
    ['French Horn', True],
    ['Trumpet', True],
    ['Trombone', True],
    ['Tuba', True],
    ['Percussion', True],
    ['Vibraphone', False],
    ['Timpani', True],
    ['Piano', True],
    ['Composer', False],
    ['Conductor', False],
    ['Harpsichord', False]
]


class InstrumentModelFactory(DjangoModelFactory):
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        If an instument kwarg is passed, get or create the instrument, else
        if instruments already exist, return a random one. Else, if they don't
        exist, create them and return a random one.
        """
        manager = cls._get_manager(model_class)
        inst = kwargs.get('instrument', None)
        if inst:
            return manager.get_or_create(instrument=inst)
        else:
            if manager.exists():
                return manager.order_by('?').first()
            else:
                for i, r in INSTRUMENT_NAMES:
                    manager.create(*args, instrument=i, show_on_roster=r)
                return manager.order_by('?').first()

    class Meta:
        model = InstrumentModel


class PersonFactory(PageFactory):
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    biography = Faker('text', max_nb_chars=200, ext_word_list=None)
    active_roster = True
    headshot = SubFactory(ImageChooserBlockFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Because this factory is always called as a subfactory, its messy to
        # pass the PersonIdx page to the called factory to be used as
        # the parent page. Therefore, it's implicitly expected that
        # a PersonIdx page already exists in the database before
        # this factory can be called.
        # This overrides the create method to add PersonIdx as the
        # parent page for all calls to PersonFactory.
        try:
            parent = PersonIndex.objects.first()
        except PersonIndex.DoesNotExist as e:
            print("PersonIndex page needs to exist in the database.")
            raise e

        kwargs['parent'] = parent
        return super()._create(model_class, *args, **kwargs)

    @post_generation
    def add_instrument(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for e in extracted:
                obj.instrument.add(e)
                obj.save_revision().publish()
        else:
            obj.instrument.add(InstrumentModelFactory())
            obj.save_revision().publish()

    class Meta:
        model = Person


class CompositionFactory(DjangoModelFactory):
    title = Faker('sentence')
    composer = SubFactory(PersonFactory)

    class Meta:
        model = Composition


class PerformerFactory(DjangoModelFactory):
    performance = None
    person = SubFactory(PersonFactory)
    instrument = SubFactory(InstrumentModelFactory)

    class Meta:
        model = Performer


class PerformanceFactory(PageFactory):
    composition = SubFactory(CompositionFactory)
    conductor = SubFactory(PersonFactory)
    performer = RelatedFactory(PerformerFactory, 'performance')

    @post_generation
    def add_performance_date(obj, create, extracted, **kwargs):
        if not create:
            obj.save_revision().publish()
            return
        else:
            concert_date = obj.get_parent().concert_date.first()
            obj.performance_date.add(concert_date)
            obj.save_revision().publish()

    class Meta:
        model = Performance


class ConcertDateFactory(DjangoModelFactory):
    concert = None
    date = Faker('future_datetime', end_date="+1y", tzinfo=TZ)

    class Meta:
        model = ConcertDate


class ConcertFactory(PageFactory):
    title = Faker('word')
    promo_copy = Faker('text', max_nb_chars=200, ext_word_list=None)
    description = Faker('text', max_nb_chars=200, ext_word_list=None)
    venue = Faker('text', max_nb_chars=200, ext_word_list=None)
    concert_image = SubFactory(ImageChooserBlockFactory)

    @post_generation
    def dates(obj, create, extracted, **kwargs):
        if create:
            if extracted:
                for date in extracted:
                    ConcertDateFactory(concert=obj, date=date)
            else:
                ConcertDateFactory(concert=obj)

        obj.save_revision().publish()

    @post_generation
    def create_roster(obj, create, extracted, **kwargs):
        if create:
            # Check if People exist, if not make some, else asign some
            if ActiveRosterMusician.objects.exists():
                obj.roster.add(
                    ActiveRosterMusician.objects.order_by('?').first()
                )
                obj.save_revision().publish()
            else:
                for p in range(25):
                    PersonFactory()

                obj.roster.add(
                    ActiveRosterMusician.objects.order_by('?').first()
                )
                obj.save_revision().publish()
        else:
            return
        if extracted:
            for i in extracted:
                obj.roster.add(i)
                obj.save_revision().publish()

    @post_generation
    def create_performances(obj, create, extracted, **kwargs):
        if not create:
            return
        else:
            # Create four performances for each concert
            PerformanceFactory(parent=obj)
            PerformanceFactory(parent=obj)
            PerformanceFactory(parent=obj)
            PerformanceFactory(parent=obj)

    class Meta:
        model = Concert


class BlogPostFactory(PageFactory):
    title = Faker('sentence')
    author = SubFactory(PersonFactory)
    date = Faker('future_date', tzinfo=TZ)
    promo_copy = Faker('paragraph')
    body = Faker('paragraph')

    class Meta:
        model = BlogPost


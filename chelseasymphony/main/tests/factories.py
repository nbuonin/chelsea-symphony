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
                for i in INSTRUMENT_NAMES:
                    manager.create(*args, instrument=i)
                return manager.order_by('?').first()

    class Meta:
        model = InstrumentModel


class PersonFactory(PageFactory):
    first_name = faker.first_name()
    last_name = faker.last_name()
    biography = faker.text(max_nb_chars=200, ext_word_list=None)
    active_roster = True
    headshot = SubFactory(ImageChooserBlockFactory)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        # Unexplainably, this factory does return unique names with each call.
        # Hacking the kwargs in this way does seem to get it to work though.
        kwargs['first_name'] = faker.first_name()
        kwargs['last_name'] = faker.last_name()
        return kwargs

    @post_generation
    def parent(self, create, extracted, **kwargs):
        """
        This is overriden from the MP_Factory base class in wagtail-factories.
        If no parent is passed, this assumes that a person index already
        exists, and that should be its parent.
        """
        if create:
            if extracted and kwargs:
                raise ValueError("Can't pass a parent instance and attributes")

            if kwargs:
                parent = self._parent_factory(**kwargs)
            else:
                if extracted:
                    parent = extracted
                else:
                    # If no parent is passed, try using the Person index
                    parent = PersonIndex.objects.first()

            if parent:
                parent.add_child(instance=self)
            else:
                type(self).add_root(instance=self)

            del self._parent_factory

    @post_generation
    def instrument(self, create, extracted, **kwargs):
        if not create:
           return
        if extracted:
            for e in extracted:
                self.instrument.add(e)
        else:
            self.instrument.add(InstrumentModelFactory())


    class Meta:
        model = Person


class CompositionFactory(DjangoModelFactory):
    title = ' '.join(faker.words())
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
    title = ' '.join(faker.words())
    conductor = SubFactory(PersonFactory)
    performer = RelatedFactory(PerformerFactory, 'performance')

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        # Unexplainably, this factory does return unique names with each call.
        # Hacking the kwargs in this way does seem to get it to work though.
        kwargs['title'] = faker.word()
        return kwargs

    @post_generation
    def performance_date(self, create, extracted, **kwargs):
        if not create:
            return
        else:
            concert_date = self.get_parent().concert_date.first()
            self.performance_date.add(concert_date)

    # @post_generation
    # def performer(self, create, extracted, **kwargs):
        # if not create:
            # return
        # else:
            # self.performer.add(PerformerFactory())


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
    title = faker.word()
    description = faker.text(max_nb_chars=200, ext_word_list=None)
    venue = faker.text(max_nb_chars=200, ext_word_list=None)
    concert_image = SubFactory(ImageChooserBlockFactory)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        # Unexplainably, this factory does return unique names with each call.
        # Hacking the kwargs in this way does seem to get it to work though.
        kwargs['title'] = faker.word()
        return kwargs

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

    @post_generation
    def create_performances(self, create, extracted, **kwargs):
        if not create:
            return
        else:
            # Create a performance for each concert
            # Because of bugginess in my code, or the factories, I can't
            # generate more than one performance.
            PerformanceFactory(parent=self)
            return

    class Meta:
        model = Concert
        exclude = ('future',)


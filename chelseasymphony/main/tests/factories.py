import factory
from faker import Factory

from chelseasymphony.main.models import (
    Home, BasicPage, ConcertDate, ConcertIndex, Concert,
    Performance, Performer, Composition, Person, PersonIndex,
    InstrumentModel, BlogPost, BlogIndex, ActiveRosterMusician
)

faker = Factory.create()

class BasicPageFactory(factory.DjangoModelFactory):
    class Meta:
        model = BasicPage

   title = faker.word()
   body = faker.text()

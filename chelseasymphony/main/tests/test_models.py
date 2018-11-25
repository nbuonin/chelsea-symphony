from datetime import (
    datetime, timedelta
)
from django.utils.timezone import get_current_timezone
from django.apps import apps
from django.test import Client
from wagtail.tests.utils import WagtailPageTests
from wagtail.core.models import Page, Site
from chelseasymphony.main.models import (
    Home, BasicPage, ConcertDate, ConcertIndex, Concert,
    Performance, Performer, Composition, Person, PersonIndex,
    InstrumentModel, BlogPost, BlogIndex, ActiveRosterMusician
)
from chelseasymphony.main.tests.factories import (
    PersonFactory, ConcertFactory, BlogPostFactory
)

from faker import Factory
faker = Factory.create()

c = Client()

ContentType = apps.get_model('contenttypes.ContentType')

def create_base_site():
    """
    This returns a tuple of:
    (homepage, concert_index, person_index)
    """
    Page.objects.filter(id=2).delete()
    Site.objects.all().delete()
    homepage_content_type, __ = ContentType.objects.get_or_create(
        model='home', app_label='main')

    homepage = Home.objects.create(
        title="Home Page",
        draft_title="Home Page",
        slug="",
        content_type=homepage_content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/",
    )
    Site.objects.create(
        hostname="localhost",
        root_page=homepage,
        is_default_site=True
    )
    c_idx = ConcertIndex(
        title="Concert Index",
        slug="concerts"
    )
    homepage.add_child(instance=c_idx)
    c_idx.save_revision().publish()

    p_idx = PersonIndex(
        title="Person Index",
        slug="people"
    )
    homepage.add_child(instance=p_idx)
    p_idx.save_revision().publish()

    b_idx = BlogIndex(
        title="Blog Index",
        slug="blog"
    )
    homepage.add_child(instance=b_idx)
    b_idx.save_revision().publish()

    return (homepage, c_idx, p_idx, b_idx)


class HomeTest(WagtailPageTests):
    @classmethod
    def setUpTestData(cls):
        cls.homepage, cls.c_idx, cls.p_idx, cls.b_idx = create_base_site()

    def test_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            Home,
            {apps.get_model('wagtailcore.Page')}
        )

    def test_subpage_types(self):
        self.assertAllowedSubpageTypes(
            Home,
            {ConcertIndex, PersonIndex, BlogIndex, BasicPage}
        )

    def test_only_one_instance(self):
        assert(Home.can_create_at(self.homepage) == False)

    def test_context(self):
        # Creates three concert series in the future, each starting one week
        # apart from each other. Also creates one concert in the past.
        # This tests that the soonest concert appears as the featured concert
        tz = get_current_timezone()
        day = timedelta(days=+1)
        week = timedelta(days=+7)

        # Create a concert at some point in the future.
        d = faker.future_date(end_date="+1y")
        c1_d1 = datetime(
            year=d.year, month=d.month, day=d.day, hour=20, tzinfo=tz)
        c1_d2 = c1_d1 + day
        c1 = ConcertFactory(
            parent=self.c_idx,
            dates=[c1_d1, c1_d2]
        )

        # Then create some more concerts, all one week apart from each other.
        c2_d1 = c1_d1 + week
        c2_d2 = c2_d1 + day
        c2 = ConcertFactory(
            parent=self.c_idx,
            dates=[c2_d1, c2_d2]
        )

        c3_d1 = c2_d1 + week
        c3_d2 = c3_d1 + day
        c3 = ConcertFactory(
            parent=self.c_idx,
            dates=[c3_d1, c3_d2]
        )

        c4_d1 = c3_d1 + week
        c4_d2 = c4_d1 + day
        c4 = ConcertFactory(
            parent=self.c_idx,
            dates=[c4_d1, c4_d2]
        )

        # Creates a concert at some past date, test that this does not appear
        c5_d = faker.date_between(start_date="-1y", end_date="-2d")
        c5_d1 = datetime(
            year=c5_d.year, month=c5_d.month, day=c5_d.day, hour=20, tzinfo=tz)
        c5_d2 = c5_d1 + day
        c5 = ConcertFactory(
            parent=self.c_idx,
            dates=[c5_d1, c5_d2]
        )

        # Create some blog posts
        b1 = BlogPostFactory(parent=self.b_idx)
        b2 = BlogPostFactory(parent=self.b_idx)

        response = c.get(self.homepage.url)
        ctx = response.context
        featured_concert = ctx['featured_concert']
        upcoming_concerts = ctx['upcoming_concerts']
        recent_blog_posts = ctx['recent_blog_posts']

        # Assert next concert is the featured concert
        assert(c1 == featured_concert)

        # Assert the size of upcoming concerts
        assert(len(upcoming_concerts) == 3)

        # Assert the next future concerts are in the correct postiitons
        assert(c2 == upcoming_concerts[0])
        assert(c3 == upcoming_concerts[1])
        assert(c4 == upcoming_concerts[2])

        # Assert that the past concert isn't published on the homepage
        assert(c5 != featured_concert)
        assert(c5 not in upcoming_concerts)

        # Assert the size of recent blog posts
        assert(len(recent_blog_posts) == 2)

        # Assert that blog posts appear on the homepage
        assert(b1 in recent_blog_posts)
        assert(b2 in recent_blog_posts)


class BasicPageTest(WagtailPageTests):
    def test_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            BasicPage,
            {Home}
        )


class ConcertIndexTest(WagtailPageTests):
    def setUp(self):
        self.homepage = Home.objects.create(
            title="Home Page",
            path="/",
            depth="1"
        )
        Site = apps.get_model('wagtailcore.Site')
        # Delete the bootstrapped site first, then create our own
        Site.objects.all().delete()
        Site.objects.create(
            hostname="localhost",
            root_page=self.homepage,
            is_default_site=True
        )
        concerts = ConcertIndex(title="Concerts")
        self.homepage.add_child(instance=concerts)
        concerts.save()


    def test_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            ConcertIndex,
            {Home}
        )

    def test_subpage_types(self):
        self.assertAllowedSubpageTypes(
            ConcertIndex,
            {Concert}
        )

    def test_only_one_instance(self):
        assert(ConcertIndex.can_create_at(self.homepage) == False)

    def test_context(self):
        assert(True)


class ConcertTest(WagtailPageTests):
    def setUp(self):
        pass

    def test_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            Concert,
            {ConcertIndex}
        )

    def test_subpage_types(self):
        self.assertAllowedSubpageTypes(
            Concert,
            {Performance}
        )

    def test_calculate_season(self):
        pass

    def test_get_context(self):
        pass

    def test_performances_by_date(self):
        pass

    def test_clean(self):
        # test that the calculated_season value gets assigned to self.season
        pass

    def test_future_concerts(self):
        # test Concert.objects.future_concerts()
        pass


class PerformanceTest(WagtailPageTests):
    def setUp(self):
        pass

    def test_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            Performance,
            {Concert}
        )

    def test_subpage_types(self):
        self.assertAllowedSubpageTypes(
            Performance,
            {}
        )

    def test_admin_form(self):
        # Create a test client to login and navigate to a Performance create page.
        # Check two things:
        # * that the performance date checkboxes are the parent concert dates
        # * the slug field is set to 'default-slug'
        pass

    def test_clean(self):
        # Check that the title matches the compostion title and then check that
        # the slug is set to the slugified version of the title
        pass

    def test_get_url_parts(self):
        # Check that the url returned is that of the parent Concert instance
        pass


class PersonTest(WagtailPageTests):
    def setUp(self):
        pass

    def test_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            Person,
            {PersonIndex}
        )

    def test_subpage_types(self):
        self.assertAllowedSubpageTypes(
            Person,
            {}
        )


class PersonIndexTest(WagtailPageTests):
    def test_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            PersonIndex,
            {Home}
        )

    def test_subpage_types(self):
        self.assertAllowedSubpageTypes(
            PersonIndex,
            {Person}
        )


class BlogPostTest(WagtailPageTests):
    def setUp(self):
        pass

    def test_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            BlogPost,
            {BlogIndex}
        )

    def test_subpage_types(self):
        self.assertAllowedSubpageTypes(
            BlogPost,
            {}
        )


class ActiveRosterMusicianTest(WagtailPageTests):
    def setUp(self):
        # Create some people who are and are not on active roster. Then assert
        # that the number of ActiveRosterMusician.objects.all() makes sense.
        pass

    def test_get_queryset(self):
        pass

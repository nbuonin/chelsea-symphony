from datetime import (
    datetime, timedelta
)
from django.utils.timezone import get_current_timezone
from django.apps import apps
from django.utils.text import slugify
from wagtail.tests.utils import WagtailPageTests
from wagtail.core.models import Page, Site
from chelseasymphony.main.models import (
    Home, BasicPage, ConcertDate, ConcertIndex, Concert,
    Performance, Performer, Composition, Person, PersonIndex,
    InstrumentModel, BlogPost, BlogIndex, ActiveRosterMusician,
    Donate, FormPage, NewMemberRequestPage
)
from chelseasymphony.main.tests.factories import (
    PersonFactory, ConcertFactory, BlogPostFactory
)

from faker import Factory
faker = Factory.create()

TZ = get_current_timezone()

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
        slug="musicians"
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


def create_future_concerts(c_idx):
    # Creates four concert series in the future, each starting one week
    # apart from each other.
    day = timedelta(days=+1)
    week = timedelta(days=+7)

    # Create a concert at some point in the future.
    d = faker.future_date(end_date="+1y", tzinfo=TZ)
    c1_d1 = datetime(
        year=d.year, month=d.month, day=d.day, hour=20, tzinfo=TZ)
    c1_d2 = c1_d1 + day
    c1 = ConcertFactory(
        parent=c_idx,
        dates=[c1_d1, c1_d2]
    )

    # Then create some more concerts, all one week apart from each other.
    c2_d1 = c1_d1 + week
    c2_d2 = c2_d1 + day
    c2 = ConcertFactory(
        parent=c_idx,
        dates=[c2_d1, c2_d2]
    )

    c3_d1 = c2_d1 + week
    c3_d2 = c3_d1 + day
    c3 = ConcertFactory(
        parent=c_idx,
        dates=[c3_d1, c3_d2]
    )

    c4_d1 = c3_d1 + week
    c4_d2 = c4_d1 + day
    c4 = ConcertFactory(
        parent=c_idx,
        dates=[c4_d1, c4_d2]
    )

    return (c1, c2, c3, c4)


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
            {ConcertIndex, PersonIndex, BlogIndex, BasicPage,
             Donate, FormPage, NewMemberRequestPage}
        )

    def test_context(self):
        c1, c2, c3, c4 = create_future_concerts(self.c_idx)
        day = timedelta(days=+1)

        # Creates a concert at some past date, test that this does not appear
        c5_d = faker.date_between(start_date="-1y", end_date="-2d")
        c5_d1 = datetime(
            year=c5_d.year, month=c5_d.month, day=c5_d.day, hour=20, tzinfo=TZ)
        c5_d2 = c5_d1 + day
        c5 = ConcertFactory(
            parent=self.c_idx,
            dates=[c5_d1, c5_d2]
        )

        # Create some blog posts
        b1 = BlogPostFactory(parent=self.b_idx)
        b2 = BlogPostFactory(parent=self.b_idx)

        response = self.client.get(self.homepage.url)
        self.assertEqual(response.status_code, 200)
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

        # Test that partial listings of concerts are returned.
        # Delete two concerts, expect that of the two remaining, one is
        # returned as a featured concert, and the other as an upcoming concert
        c1.delete()
        c2.delete()

        response = self.client.get(self.homepage.url)
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        featured_concert = ctx['featured_concert']
        upcoming_concerts = ctx['upcoming_concerts']
        recent_blog_posts = ctx['recent_blog_posts']

        assert(c3 == featured_concert)
        assert(c4 == upcoming_concerts[0])

        # Test that no exceptions are thrown when no future concerts exist
        c3.delete()
        c4.delete()

        response = self.client.get(self.homepage.url)
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        featured_concert = ctx['featured_concert']
        upcoming_concerts = ctx['upcoming_concerts']
        recent_blog_posts = ctx['recent_blog_posts']

        self.assertIsNone(featured_concert)
        assert(len(upcoming_concerts) == 0)


class ConcertIndexTest(WagtailPageTests):
    @classmethod
    def setUpTestData(cls):
        cls.homepage, cls.c_idx, cls.p_idx, cls.b_idx = create_base_site()

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
    @classmethod
    def setUpTestData(cls):
        cls.homepage, cls.c_idx, cls.p_idx, cls.b_idx = create_base_site()
        cls.c1, cls.c2, cls.c3, cls.c4 = create_future_concerts(cls.c_idx)

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
        # The concert season begins on the Aug 1 of each year
        d1 = datetime(year=2018, month=7, day=1, hour=20, minute=0, tzinfo=TZ)
        d1_season = Concert.calculate_season(d1)
        assert(d1_season == '2017-2018')

        d2 = datetime(year=2018, month=8, day=1, hour=20, minute=0, tzinfo=TZ)
        d2_season = Concert.calculate_season(d2)
        assert(d2_season == '2018-2019')

    def test_get_context(self):
        response = self.client.get(self.c1.get_url())
        self.assertEqual(response.status_code, 200)
        ctx = response.context

        # Get performances and check conductor names
        conductor_names = [c['name'] for c in ctx['conductors']]
        for p in self.c1.get_children().specific():
            assert(p.conductor.title in conductor_names)

        # Check the program by checking performance names
        performance_titles = [p['composition'] for p in ctx['program']]
        for p in self.c1.get_children().specific():
            assert(p.title in performance_titles)

        # Check the performer names
        performer_names = [p['name'] for p in ctx['performers']]
        for p in self.c1.get_children().specific():
            for performer in p.performer.all():
                assert performer.person.title in performer_names

    def test_performances_by_date(self):
        """
        The performances_by_date method should return a dict that looks like:
            date
            program:
              * composer
              * composition
              * performers:
                * name
                * url
                * instrument
        """
        dates = [p['date'] for p in self.c1.performances_by_date()]
        for d in [d.date for d in self.c1.concert_date.all()]:
            assert d in dates

        # Assert the keys of the interface
        assert 'date' in self.c1.performances_by_date()[0].keys()
        assert 'program' in self.c1.performances_by_date()[0].keys()
        assert 'composer' in \
            self.c1.performances_by_date()[0]['program'][0].keys()
        assert 'composition' in \
            self.c1.performances_by_date()[0]['program'][0].keys()
        assert 'performers' in \
            self.c1.performances_by_date()[0]['program'][0].keys()

        a_performer = self.c1.performances_by_date()[0]\
            ['program'][0]['performers'][0].keys()
        assert 'name' in a_performer
        assert 'url' in a_performer
        assert 'instrument' in a_performer

    def test_clean(self):
        # test that the calculated_season value gets assigned to self.season
        c = ConcertFactory()
        assert(c.season)

    def test_get_url_parts(self):
        model_season = self.c1.season
        _, _, path = self.c1.get_url_parts()
        path_season = path.split('/')[-3]
        self.assertEqual(model_season, path_season)

    def test_future_concerts(self):
        # test Concert.objects.future_concerts()
        fc = Concert.objects.future_concerts()
        assert(len(fc) == 4)
        assert(self.c1 == fc[0])
        assert(self.c2 == fc[1])
        assert(self.c3 == fc[2])
        assert(self.c4 == fc[3])


class NextEventTest(WagtailPageTests):
    @classmethod
    def setUpTestData(cls):
        cls.homepage, cls.c_idx, cls.p_idx, cls.b_idx = create_base_site()

    def test_next_redirect(self):
        c1, _, _, _ = create_future_concerts(self.c_idx)

        r1 = self.client.get('/whats-next/')
        self.assertRedirects(r1, c1.get_url())

        r2 = self.client.get('/whats-next/?foo=bar')
        self.assertRedirects(r2, c1.get_url() + '?foo=bar')

    def test_no_future_event(self):
        r1 = self.client.get('/whats-next/')
        self.assertRedirects(r1, self.c_idx.get_url())

        r2 = self.client.get('/whats-next/?foo=bar')
        self.assertRedirects(r2, self.c_idx.get_url() + '?foo=bar')

class PerformanceTest(WagtailPageTests):
    @classmethod
    def setUpTestData(cls):
        cls.homepage, cls.c_idx, cls.p_idx, cls.b_idx = create_base_site()
        cls.c1, cls.c2, cls.c3, cls.c4 = create_future_concerts(cls.c_idx)

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
        perf = self.c1.get_descendants().first().specific
        self.assertEquals(
            perf.title,
            perf.composition.title
        )
        self.assertEquals(
            perf.slug,
            slugify(perf.title)
        )

        perf.composition.title = "Foo Bar"
        perf.composition.save()
        perf.save_revision().publish()
        self.assertEquals(
            perf.title,
            "Foo Bar"
        )
        self.assertEquals(
            perf.slug,
            "foo-bar"
        )

    def test_get_url_parts(self):
        # Check that the url returned is that of the parent Concert instance
        self.assertEquals(
            self.c2.get_url_parts(),
            self.c2.get_descendants().first().specific.get_url_parts()
        )


class PersonTest(WagtailPageTests):
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
            {Person, BasicPage}
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

from django.apps import apps
from wagtail.tests.utils import WagtailPageTests
from wagtail.core.models import Page
from chelseasymphony.main.models import (
    Home, BasicPage, ConcertDate, ConcertIndex, Concert,
    Performance, Performer, Composition, Person, PersonIndex,
    InstrumentModel, BlogPost, BlogIndex, ActiveRosterMusician
)

class HomeTest(WagtailPageTests):
    def setUp(self):
        homepage = Home.objects.create(
            title="Home Page",
            path="/",
            depth="1"
        )
        Site = apps.get_model('wagtailcore.Site')
        Site.objects.all().delete()
        Site.objects.create(
            hostname="localhost",
            root_page=homepage,
            is_default_site=True
        )


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
        root = Page.objects.get(id=1)
        assert(Home.can_create_at(root) == False)

    def test_context(self):
        assert(True)


class BasicPageTest(WagtailPageTests):
    def setUp(self):
        pass

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

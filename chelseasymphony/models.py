from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel \
    InlinePanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet


class Home(Page):
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner_image')
    ]

    parent_page_types = [chelseasymphony.Concert]
    subpage_types = []


class Concert(Page):
    title = RichTextField()
    description =
    venue =
    performances =
    image =
    dates =

    @property
    def conductors():
        pass


@register_snippet
class Performance(models.Model):
    pass


@register_snippet
class Performer(models.Model):
    pass


@register_snippet
class Composition(models.Model):
    pass


class Person(Page):
    pass


@register_snippet
class Instrument(models.Model):
    pass

from django.db import models

from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel


class Home(Page):
    text = models.CharField(max_length=255)

    content_panels = Page.content_panels + [
        FieldPanel('text', classname="full")
    ]

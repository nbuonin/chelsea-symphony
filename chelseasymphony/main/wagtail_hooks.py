"""Implements hooks"""
import logging
from django.core.mail import send_mail
from django.db.models import Min
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from wagtail.core import hooks
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from wagtail.contrib.modeladmin.mixins import ThumbnailMixin
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import (
    valid_ipn_received, invalid_ipn_received
)
from .models import (
    Person, Composition, InstrumentModel, Concert, ConcertIndex
)
logger = logging.getLogger('django.server')


class ConcertAdmin(ModelAdmin):
    """Creates admin page for concerts"""
    model = Concert
    menu_label = 'Concerts'
    menu_icon = 'date'
    menu_order = 200
    exclude_from_explorer = True
    list_display = ('admin_title', 'concert_dates')
    list_filter = ('season',)
    search_fields = ('title', 'description')


class PersonAdmin(ThumbnailMixin, ModelAdmin):
    """Creates admin page for people"""
    model = Person
    menu_label = 'People'
    menu_icon = 'group'
    menu_order = 205
    exclude_from_explorer = True
    list_display = ('admin_thumb', 'first_name', 'last_name')
    list_display_add_buttons = 'first_name'
    thumb_image_field_name = 'headshot'
    list_filter = ('active_roster',)
    search_fields = ('first_name', 'last_name')


class CompositionAdmin(ModelAdmin):
    """Creates admin page for compositions"""
    model = Composition
    menu_label = 'Compositions'
    menu_icon = 'doc-full-inverse'
    menu_order = 210
    exclude_from_explorer = True
    list_display = ('display_title', 'composer')
    list_filter = ('composer',)
    search_fields = ('title',)


class InstrumentAdmin(ModelAdmin):
    """Creates admin page for instruments"""
    model = InstrumentModel
    menu_label = 'Instruments'
    menu_icon = 'pick'
    menu_order = 220
    exclude_from_explorer = True
    list_display = ('instrument',)
    list_filter = ('show_on_roster',)


@hooks.register('construct_main_menu')
def hide_snippets_menu_item(request, menu_items):
    """Hide the snippets menu

    Admin menus for models used as snippets are rendered as model admins.
    Therefore we don't need the snippets menu
    """
    menu_items[:] = [item for item in menu_items if item.name != 'snippets']


@hooks.register('construct_explorer_page_queryset')
def order_concert_performances(parent_page, pages, request):
    """
    This orders performance pages by the tree path order. This is the order
    that performances are displayed, and so we want to preserve
    that for the editor.
    """
    if isinstance(parent_page, Concert):
        pages = pages.order_by('path')

    return pages


@hooks.register('construct_explorer_page_queryset')
def order_concerts(parent_page, pages, request):
    """
    This orders concerts by the first concert date
    """
    if isinstance(parent_page, ConcertIndex):
        pages = pages.annotate(
            first_date=Min('concert__concert_date__date')).\
            order_by('-first_date')

    return pages


@hooks.register('after_create_page')
def redirect_pages_to_admin(request, page):
    """Redirect on page creation

    After creating a new page, except for Person pages, redirect to
    the explorer admin for that page, rather than the parent page in the tree.

    Person pages DO get redirected to the parent 'listing' page.
    """
    if not isinstance(page, Person):
        return HttpResponseRedirect('/admin/pages/{}/'.format(page.id))

    return HttpResponseRedirect('/admin/main/person/')


@hooks.register('after_edit_page')
def redirect_pages_to_admin_edit(request, page):
    """Redirect on page edit

    After editing a page, except for Person pages, redirect to
    the explorer admin for that page, rather than the parent page in the tree.

    Person pages DO get redirected to the parent 'listing' page.
    """
    if not isinstance(page, Person):
        return HttpResponseRedirect('/admin/pages/{}/'.format(page.id))

    return HttpResponseRedirect('/admin/main/person/')


def handle_donation(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        if ipn_obj.receiver_email != settings.PAYPAL_ACCT_EMAIL:
            plaintext = get_template('main/email/donation_confirmation.txt')
            ctx = {
                'first_name': ipn_obj.first_name,
                'last_name': ipn_obj.last_name,
                'email_address': ipn_obj.payer_email,
                'amount': ipn_obj.amount
            }
            send_mail(
                'Thank you for your donation',
                plaintext.render(ctx),
                settings.DONATION_EMAIL_ADDR,
                [ipn_obj.payer_email],
            )


def handle_invalid_donation(sender, **kwargs):
    logger.info('An invalid IPN request was made')


modeladmin_register(ConcertAdmin)
modeladmin_register(PersonAdmin)
modeladmin_register(CompositionAdmin)
modeladmin_register(InstrumentAdmin)
valid_ipn_received.connect(handle_donation)
invalid_ipn_received.connect(handle_invalid_donation)

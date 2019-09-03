"""Implements hooks"""
import logging
from django.core.mail import send_mail
from django.db.models import Min
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.utils.timezone import localtime
from django.conf import settings
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.core import hooks
from wagtail.contrib.modeladmin.helpers import (
    PermissionHelper, PageButtonHelper
)
from wagtail.contrib.modeladmin.mixins import ThumbnailMixin
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import (
    valid_ipn_received, invalid_ipn_received
)
from paypal.standard.ipn.models import PayPalIPN
from .models import (
    Person, Composition, InstrumentModel, Concert, ConcertIndex,
    ConcertDate, Performance, NewMemberRequest, BlogPost
)
logger = logging.getLogger('django.server')


class ProtectModelPermissionHelper(PermissionHelper):
    def user_can_create(self, user):
        return False

    def user_can_edit_obj(self, user, obj):
        return False

    def user_can_delete_obj(self, user, obj):
        return False


class ConcertButtonHelper(PageButtonHelper):
    """Override to add 'View Live' and 'Explore' buttons"""
    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        btns = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude)

        extra_btns = [
            {
                'url': obj.get_url(),
                'label': 'View Live',
                'classname': 'button button-small button-secondary',
                'title': 'View Live'
            },
            {
                'url': '/admin/pages/{}/'.format(obj.id),
                'label': 'Explore',
                'classname': 'button button-small button-secondary',
                'title': 'Explore'
            }
        ]
        return extra_btns + btns


class ConcertAdmin(ModelAdmin):
    """Creates admin page for concerts"""
    button_helper_class = ConcertButtonHelper

    model = Concert
    menu_label = 'Concerts'
    menu_icon = 'date'
    menu_order = 200
    exclude_from_explorer = True
    list_display = ('title', 'concert_dates', 'season')
    list_filter = ('season',)
    search_fields = ('title', 'description')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            first_date=Min('concert_date__date')).\
            order_by('-first_date')

    def concert_dates(self, obj):
        dates = ConcertDate.objects.\
            filter(concert=obj.id).order_by('date')

        return '; '.join(
            [localtime(d.date).
             strftime('%a, %b %d, %-I:%M %p, %Y') for d in dates])


class ViewLiveButtonHelper(PageButtonHelper):
    """Override to add 'View Live' button"""
    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        btns = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude)

        extra_btns = [
            {
                'url': obj.get_url(),
                'label': 'View Live',
                'classname': 'button button-small button-secondary',
                'title': 'View Live'
            },
        ]
        return extra_btns + btns


class PersonAdmin(ThumbnailMixin, ModelAdmin):
    """Creates admin page for people"""
    button_helper_class = ViewLiveButtonHelper

    model = Person
    menu_label = 'People'
    menu_icon = 'group'
    menu_order = 205
    exclude_from_explorer = True
    list_display = (
        'admin_thumb', 'first_name', 'last_name', 'instrument_list')
    list_display_add_buttons = 'first_name'
    thumb_image_field_name = 'headshot'
    list_filter = ('active_roster', 'instrument')
    search_fields = ('first_name', 'last_name')
    ordering = ('last_name',)

    def instrument_list(self, obj):
        return ', '.join([i.instrument for i in obj.instrument.all()])

    instrument_list.short_description = 'Instrument'


class CompositionAdmin(ModelAdmin):
    """Creates admin page for compositions"""
    model = Composition
    menu_label = 'Compositions'
    menu_icon = 'doc-full-inverse'
    menu_order = 210
    exclude_from_explorer = True
    list_display = ('display_title', 'composer')
    search_fields = ('title', 'composer__title')


class BlogPostAdmin(ModelAdmin):
    """Creates admin page for blog posts"""
    button_helper_class = ViewLiveButtonHelper

    model = BlogPost
    menu_label = 'Blog Posts'
    menu_icon = 'doc-full-inverse'
    menu_order = 215
    exclude_from_explorer = True
    list_display = ('title', 'date', 'author')
    search_fields = ('title', 'author', 'promo_copy', 'body')
    ordering = ('-date', )


class InstrumentAdmin(ModelAdmin):
    """Creates admin page for instruments"""
    model = InstrumentModel
    menu_label = 'Instruments'
    menu_icon = 'pick'
    menu_order = 220
    exclude_from_explorer = True
    list_display = ('instrument', 'weight')
    ordering = ('weight',)
    list_filter = ('show_on_roster',)


class NewMemberRequestAdmin(ModelAdmin):
    """Creates an admin for new member submissions"""
    permission_helper_class = ProtectModelPermissionHelper
    model = NewMemberRequest
    menu_label = 'New Member Requests'
    menu_icon = 'user'
    menu_order = 225
    list_display = (
        'created_at', 'first_name', 'last_name', 'email', 'instrument',
        'resume', 'source', 'link', 'read_policies'
    )
    list_filter = ('instrument', 'source')
    search_fields = ('first_name', 'last_name')


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
    if isinstance(page, Performance):
        return HttpResponseRedirect(
            '/admin/pages/{}/'.format(page.get_parent().id))

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
    if isinstance(page, Performance):
        return HttpResponseRedirect(
            '/admin/pages/{}/'.format(page.get_parent().id))

    if not isinstance(page, Person):
        return HttpResponseRedirect('/admin/pages/{}/'.format(page.id))

    return HttpResponseRedirect('/admin/main/person/')


class EditChildrenMenuItem(ActionMenuItem):
    name = 'edit-children'
    label = 'Edit Children'

    def is_shown(self, request, context):
        if context['view'] == 'create':
            return False

        if not isinstance(context['page'], Concert):
            return False

        return True

    def get_url(self, request, context):
        page = context['page']
        _, base_url, _ = page.get_url_parts()
        return '{}/admin/pages/{}/'.format(base_url, page.id)


@hooks.register('register_page_action_menu_item')
def edit_children():
    return EditChildrenMenuItem(order=100)


def handle_donation(sender, **kwargs):
    ipn_obj = sender
    ctx = {
        'first_name': ipn_obj.first_name,
        'last_name': ipn_obj.last_name,
        'email_address': ipn_obj.payer_email,
        'amount': ipn_obj.mc_gross,
        'payment_date': ipn_obj.payment_date,
        'txn_id': ipn_obj.txn_id,
    }

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        if ipn_obj.receiver_email != settings.PAYPAL_ACCT_EMAIL:
            logger.info('An invalid payment request was made')
            return

        # send email for one-time donation
        if ipn_obj.txn_type == 'web_accept':
            plaintext = get_template('main/email/donation_confirmation.txt')
            send_mail(
                'Thank you for your donation',
                plaintext.render(ctx),
                settings.DONATION_EMAIL_ADDR,
                [ipn_obj.payer_email],
            )

        # send mail for recurring donation
        if ipn_obj.txn_type == 'subscr_payment':
            plaintext = get_template(
                'main/email/recurring_donation_confirmation.txt')
            send_mail(
                'Thank you for your donation',
                plaintext.render(ctx),
                settings.DONATION_EMAIL_ADDR,
                [ipn_obj.payer_email],
            )

    # send mail for new recurring donation signup
    if ipn_obj.txn_type == 'subscr_signup':
        plaintext = get_template('main/email/recurring_donation_welcome.txt')
        send_mail(
            'Thank you for your recurring donation',
            plaintext.render(ctx),
            settings.DONATION_EMAIL_ADDR,
            [ipn_obj.payer_email],
        )


def handle_invalid_donation(sender, **kwargs):
    logger.info('An invalid IPN request was made')


class DonationAdmin(ModelAdmin):
    permission_helper_class = ProtectModelPermissionHelper
    model = PayPalIPN
    menu_label = 'Donations'
    menu_icon = 'form'
    menu_order = 230
    list_display = (
        'payment_date', 'first_name', 'last_name', 'payer_email',
        'payment_type', 'mc_gross', 'payment_status'
    )
    list_filter = ('recurring', 'payment_status')
    search_fields = ('first_name', 'last_name')
    inspect_view_enabled = True

    def recurring_donation(self, obj):
        return True if obj.recurring else False


modeladmin_register(ConcertAdmin)
modeladmin_register(PersonAdmin)
modeladmin_register(CompositionAdmin)
modeladmin_register(BlogPostAdmin)
modeladmin_register(InstrumentAdmin)
modeladmin_register(DonationAdmin)
modeladmin_register(NewMemberRequestAdmin)
valid_ipn_received.connect(handle_donation)
invalid_ipn_received.connect(handle_invalid_donation)

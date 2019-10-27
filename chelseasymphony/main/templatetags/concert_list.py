from django import template

register = template.Library()


@register.inclusion_tag('concert_list.html')
def list_concerts(concerts):
    return {'concerts': concerts}

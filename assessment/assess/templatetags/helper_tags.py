from django import template
register = template.Library()

from django.template.loader import get_template

@register.filter
def linkify(object):
    return get_template('helpers/linkify.html').render({'object': object})

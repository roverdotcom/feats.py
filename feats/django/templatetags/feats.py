from django import template
from django.apps import apps

register = template.Library()
app_config = apps.get_app_config('feats')


@register.filter
def selector_type(selector):
    name = app_config.feats_app._name(selector)
    if name in app_config.feats_app.selectors:
        return name
    else:
        raise ValueError("Selector '{}' has not been registered with the app".format(name))

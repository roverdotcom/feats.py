from django.apps import apps
from django.views.generic import base
from django import forms
from collections import defaultdict

app_config = apps.get_app_config('feats')

WIDGET_ATTRS = {'class': 'form-control'}
TEXT_WIDGET = forms.TextInput(attrs=WIDGET_ATTRS)
INTEGER_WIDGET = forms.NumberInput(attrs=WIDGET_ATTRS)
CHOICES_WIDGET = forms.Select(attrs=WIDGET_ATTRS)


class TemplateView(base.TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = app_config.feats_app.features.values()
        return context

    @property
    def feats_app(self):
        return app_config.feats_app


class Form(forms.Form):
    @property
    def fieldsets(self):
        fieldsets = defaultdict(list)
        for key, field in self.fields.items():
            fieldset = getattr(field, 'fieldset', None)
            fieldsets[fieldset].append(self[key])

        if len(fieldsets.keys() - [None]) == 0:
            return {}

        for name, fieldset in fieldsets.items():
            yield name, fieldset


class ChoiceField(forms.ChoiceField):
    def __init__(self, widget=CHOICES_WIDGET, fieldset=None, *args, **kwargs):
        super().__init__(*args, widget=widget, **kwargs)
        self.fieldset = fieldset


class IntegerField(forms.IntegerField):
    def __init__(self, widget=INTEGER_WIDGET, fieldset=None, *args, **kwargs):
        super().__init__(*args, widget=widget, **kwargs)
        self.fieldset = fieldset


class CharField(forms.CharField):
    def __init__(self, widget=TEXT_WIDGET, fieldset=None, *args, **kwargs):
        super().__init__(*args, widget=widget, **kwargs)
        self.fieldset = fieldset


class HiddenCharField(forms.CharField):
    def __init__(self, widget=forms.HiddenInput, fieldset=None, *args, **kwargs):
        super().__init__(*args, widget=widget, **kwargs)
        self.fieldset = fieldset


def parse_field(key, prefix):
    """
    Given a string of the form "{prefix}-{index}-{field_name}", returns the index and field name
    If the string does not meet this form, returns None, None
    """
    startswith, *rest = key.split(prefix, 1)
    if startswith != '' or len(rest) != 1:
        return None, None

    _, index, *rest = rest[0].split('-', 2)
    if len(rest) == 0:
        return None, None

    try:
        return int(index), rest[0]
    except ValueError:
        # Management forms don't have an index, so will start with {prefix} but won't be
        # able to parse out an integer from the second component
        return None, None


def compress_formsets(data, prefix):
    """
    The UI allows any individual row to be removed from the formset, which can leave gaps in
    the POST data. Django formsets don't work unless each index is sequential, starting from 0,
    so we need to convert the sparse array to a dense array.
    This could also be acomplished with Formset.can_delete, but would require more logic on the frontend
    """
    forms = defaultdict(dict)
    dense = {}
    for key, value in data.items():
        index, field = parse_field(key, prefix)
        if index is not None:
            forms[index][field] = value
        else:
            # Not a form field, pass the data straight through
            dense[key] = value

    form_index = 0
    for sparse_index, fields in forms.items():
        for field, value in fields.items():
            dense_key = f'{prefix}-{form_index}-{field}'
            dense[dense_key] = value
        form_index += 1

    return dense

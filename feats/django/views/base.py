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



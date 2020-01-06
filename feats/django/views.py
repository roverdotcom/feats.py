from django import forms
from django.apps import apps
from django.http.response import HttpResponseRedirect
from django.http.response import HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import base

app_config = apps.get_app_config('feats')

class TemplateView(base.TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = app_config.feats_app.features.values()
        return context

class Index(TemplateView):
    template_name = 'feats/index.html'


class Detail(TemplateView):
    template_name = 'feats/detail.html'

    @property
    def feature(self):
        return app_config.feats_app.features[self.args[0]]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feature'] = self.feature
        return context


def feature_segment_formset(feature_handle, *fn_args, **fn_kwargs):
    class FormsetForm(FeatureSegmentForm):
        def __init__(self, *args, **kwargs):
            super().__init__(feature_handle, *args, **kwargs)
    return forms.formset_factory(FormsetForm, *fn_args, **fn_kwargs)


class FeatureSegmentForm(forms.Form):
    """
    Maps a Segment to a feature. Intended to be used in a Formset 
    """

    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['segment'] = forms.ChoiceField(
            choices=[(name, name) for name, segment in feature_handle.valid_segments().items()],
            required=True
        )


class SelectorSegmentForm(forms.Form):
    """
    Maps a selector to the result of segmentation
    """
    segment = forms.CharField()


class ChangeSegmentation(TemplateView):
    template_name = 'feats/change_segmentation.html'

    @property
    def feature(self):
        return app_config.feats_app.features[self.args[0]]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature = self.feature
        context['feature'] = feature
        context['formset'] = feature_segment_formset(feature)
        return context


class StaticSelectorForm(forms.Form):
    _type = forms.CharField(
            required=True,
            widget=forms.HiddenInput,
            initial='static'
    )

    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__(*args, **kwargs)                
        self.fields['implementation'] = forms.ChoiceField(
            choices=[(name, name) for name in feature_handle.feature.implementations.keys()]
        )

    def create_selector(self):
        print("Create Static")


class RolloutSelectorForm(forms.Form):
    _type = forms.CharField(
            required=True,
            widget=forms.HiddenInput,
            initial='rollout'
    )

    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in feature_handle.feature.implementations.keys():
            self.fields['{}_weight'.format(name)] = forms.IntegerField(
                required=True,
                min_value=0,
                initial=0,
            )


    def create_selector(self):
        print("Create Rollout")


class ExperimentSelectorForm(forms.Form):
    _type = forms.CharField(
        required=True,
        widget=forms.HiddenInput,
        initial='experiment'
    )

    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in feature_handle.feature.implementations.keys():
            self.fields['{}_weight'.format(name)] = forms.IntegerField(
                required=True,
                min_value=0,
                initial=0,
            )

    def create_selector(self):
        print("Create Experiment")


class AddSelector(TemplateView):
    template_name = 'feats/add_selector.html'
    forms = {
        'experiment': ExperimentSelectorForm,
        'static': StaticSelectorForm,
        'rollout': RolloutSelectorForm,
    }

    @property
    def feature(self):
        return app_config.feats_app.features[self.args[0]]

    def create_forms(self):
        """
        Dynamically creates forms for adding each type of selector based on
        the feature it is being created for.
        For rollout & experiment selectors, there is a field per implementation
        for the weight of that implementation.
        For static selectors, the select box's options are populated with each
        implementation.
        """
        feature = self.feature
        data = {}
        if self.request.method == 'POST':
            data[self.request.POST['_type']] = self.request.POST

        init_forms = {}
        for key, form in self.forms.items():
            init_forms[key] = form(feature, data=data.get(key), auto_id='id_{}_%s'.format(key))
        return init_forms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feature'] = self.feature
        context['forms'] = self.create_forms()
        return context

    def post(self, request, *args, **kwargs):
        forms = self.create_forms()
        bound_form = None
        for form in forms.values():
            if form.is_bound:
                bound_form = form
                break

        if bound_form is None:
            return HttpResponseBadRequest()

        if bound_form.is_valid():
            form.create_selector()
            return HttpResponseRedirect(
                reverse('feats:detail', args=self.args)
            )

        return HttpResponseBadRequest()


class ChangeSelector(TemplateView):
    template_name = 'feats/change_selector.html'

    @property
    def feature(self):
        return app_config.feats_app.features[self.args[0]]

    @property
    def selector(self):
        return self.feature.selectors[int(self.args[1])]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feature'] = self.feature
        context['selector'] = self.selector
        return context

from django import forms
from django.apps import apps
from django.http.response import HttpResponseRedirect
from django.http.response import HttpResponseBadRequest
from django.http import Http404
from django.urls import reverse
from django.views.generic import base

from feats import selector
from feats.state import FeatureState

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
        feature = self.feature
        state = feature.get_current_state()
        context['feature'] = feature
        context['state'] = state
        if state:
            context['segment_names'] = [segment.name for segment in state.segments]
        return context


def feature_segment_formset(feature_handle, data=None):
    class FormsetForm(FeatureSegmentForm):
        def __init__(self, *args, **kwargs):
            super().__init__(feature_handle, *args, **kwargs)
    return forms.formset_factory(FormsetForm)(data=data, prefix='segment')


class FeatureSegmentForm(forms.Form):
    """
    Maps a Segment to a feature. Intended to be used in a Formset
    """

    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['segment'] = forms.ChoiceField(
            choices=[
                (name, name)
                for name, segment in feature_handle.valid_segments().items()
            ],
            required=True
        )

def selector_mapping_formset(segments, state, data=None):
    class FormsetForm(SelectorMappingForm):
        def __init__(self, *args, **kwargs):
            super().__init__(segments, state.selectors, *args, **kwargs) 
    return forms.formset_factory(FormsetForm)(data=data, prefix='selector-mapping')


class SelectorMappingForm(forms.Form):
    """
    Maps a selector to the result of segmentation.
    """
    def __init__(self, segments, selectors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selectors = selectors
        self.segments = segments
        self.fields['selector'] = forms.ChoiceField(
                choices=[
                    (i, selector.name)
                    for i, selector in enumerate(selectors)
                ],
                required=True
        )
        for segment in segments:
            self.fields['segment[{}]'.format(segment.name)] = forms.CharField(required=True)


    def get_mapping_entry(self):
        """
        Converts this form's cleaned_data to a k/v tuple
        mapping a segment to a selector
        """
        selector_index = int(self.cleaned_data['selector'])
        segment_values = []
        for segment in self.segments:
            segment_values.append(self.cleaned_data['segment[{}]'.format(segment.name)])
        return tuple(segment_values), self.selectors[selector_index]


class ChangeSegmentation(TemplateView):
    """
    Changes how a Feature is Segmented and how selectors map to those segments.

    Updating segmentation resets any selector mappings, so this form is done in
    two steps.
    The first form submits through a GET to this url with the segments.
        This does not save any data to the database.
    The next form submits through a POST to this url with the segments and mappings.
        This creates a new feature state and persists it.

    We update both segmentation and mapping in the same POST, as the alternative
    is to delete all mappings when segmentation is updated.
    """
    template_name = 'feats/change_segmentation.html'

    @property
    def feature(self):
        return app_config.feats_app.features[self.args[0]]

    def get_state(self, feature):
        state = feature

    def get_segment_formset(self, feature, data):
        return feature_segment_formset(feature, data=data)

    def get_mapping_formset(self, segments, state, data):
        return selector_mapping_formset(segments, state, data=data)

    def validate_and_get_segments(self, segment_formset):
        segment_names = [form.cleaned_data['segment'] for form in segment_formset]
        segments = [
            app_config.feats_app.segments[segment_name]
            for segment_name in segment_names
        ]
        return segments

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature = self.feature
        state = feature.get_current_state()
        if state is None:
            state = FeatureState(
                    segments=[],
                    selectors=[],
                    selector_mapping={},
                    created_by=self.request.user.username
            )
        segment_formset, mapping_formset = self.get_formsets(feature, state, self.request.GET)
        if mapping_formset is None:
            context['form_method'] = 'GET'
            context['formsets'] = [segment_formset]
        else:
            context['form_method'] = 'POST'
            context['formsets'] = [segment_formset, mapping_formset]
        context['feature'] = feature
        return context

    def get_formsets(self, feature, state, data):
        if not data:
            data = None
        segment_formset = self.get_segment_formset(feature, data)
        mapping_formset = None
        if segment_formset.is_bound and segment_formset.is_valid():
            segments = self.validate_and_get_segments(segment_formset)
            data = {
                k:v for k, v in data.items() if not k.startswith('segment')
            }
            if not data:
                data = None
            mapping_formset = self.get_mapping_formset(segments, state, data)

        return (segment_formset, mapping_formset)

    def post(self, request, *args, **kwargs):
        feature = self.feature
        state = feature.get_current_state()
        if state is None:
            state = FeatureState(
                    segments=[],
                    selectors=[],
                    selector_mapping={},
                    created_by=self.request.user.username
            )
        segment_formset, mapping_formset = self.get_formsets(feature, state, request.POST)
        if mapping_formset is None:
            return HttpResponseBadRequest()

        if mapping_formset.is_valid():
            segments = self.validate_and_get_segments(segment_formset)
            selector_mapping = dict(form.get_mapping_entry() for form in mapping_formset)
            state = FeatureState(
                    segments=segments,
                    selectors=state.selectors,
                    selector_mapping=selector_mapping,
                    created_by=self.request.user.username
            )
            self.feature.set_state(state)
            return HttpResponseRedirect(
                reverse('feats:detail', args=self.args)
            )

        return HttpResponseBadRequest()


class SelectorForm(forms.Form):
    name = forms.CharField(required=True)

    def __init__(self, _type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['_type'] = forms.CharField(
            required=True,
            widget=forms.HiddenInput,
            initial=_type
        )


class StaticSelectorForm(SelectorForm):
    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__('static', *args, **kwargs)
        self.feature_handle = feature_handle
        self.fields['implementation'] = forms.ChoiceField(
            choices=[
                (name, name)
                for name in feature_handle.feature.implementations.keys()
            ],
            required=True
        )

    def create_selector(self):
        return selector.Static.from_data(
            self.feature_handle.app, {
                'value': self.cleaned_data['implementation'],
                'name': self.cleaned_data['name'],
            }
        )


class WeightedSelectorForm(SelectorForm):
    def __init__(self, feature_handle, _type, *args, **kwargs):
        super().__init__(_type, *args, **kwargs)
        self.feature_handle = feature_handle
        for name in feature_handle.feature.implementations.keys():
            self.fields['weights[{}]'.format(name)] = forms.IntegerField(
                required=True,
                min_value=0,
                initial=0,
            )

    def get_weights(self):
        weights = {}
        for name in self.feature_handle.feature.implementations.keys():
            weight = self.cleaned_data['weights[{}]'.format(name)]
            weights[name] = weight
        return weights


class RolloutSelectorForm(WeightedSelectorForm):
    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__(feature_handle, 'rollout', *args, **kwargs)
        self.fields['segment'] = forms.ChoiceField(
            choices=[
                (name, name) for name in feature_handle.valid_segments().keys()
            ],
            required=True
        )

    def create_selector(self):
        segment = self.cleaned_data['segment']
        name = self.cleaned_data['name']
        weights = self.get_weights()

        return selector.Rollout.from_data(
            self.feature_handle.app, {
                'name': name,
                'weights': weights,
                'segment': segment
            }
        )


class ExperimentSelectorForm(WeightedSelectorForm):
    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__(feature_handle, 'experiment', *args, **kwargs)
        self.fields['segment'] = forms.ChoiceField(
            choices=[
                (name, name) for name in feature_handle.valid_segments().keys()
            ],
            required=True
        )

    def create_selector(self):
        segment = self.cleaned_data['segment']
        name = self.cleaned_data['name']
        weights = self.get_weights()

        return selector.Experiment.from_data(
            self.feature_handle.app, {
                'name': name,
                # Needs App support for registering persisters
                'persister': "# TODO:",
                'weights': weights,
                'segment': segment
            }
        )


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
            init_forms[key] = form(
                feature,
                data=data.get(key),
                auto_id='id_{}_%s'.format(key)
            )
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
            feature = self.feature
            selector = form.create_selector()
            state = feature.get_current_state()
            if state is None:
                state = FeatureState(
                    segments=[],
                    selectors=[selector],
                    selector_mapping={},
                    created_by=self.request.user.username
                )
            else:
                state = FeatureState(
                    segments=state.segments,
                    selectors=state.selectors + [selector],
                    selector_mapping=state.selector_mapping,
                    created_by=self.request.user.username
                )
            self.feature.set_state(state)
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
    def state(self):
        state = self.feature.get_current_state()
        if state is None:
            raise Http404()
        return state

    @property
    def form(self):
        return self.state.selectors[int(self.args[1])]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feature'] = self.feature
        context['form'] = self.form
        context['selector'] = self.selector
        return context

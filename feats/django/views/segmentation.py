from django.forms.formsets import BaseFormSet
from django.forms import formset_factory
from django.http.response import HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse
from feats.state import FeatureState

from feats.django.views import base


class FeatureSegmentFormset(BaseFormSet):
    def validate_and_get_segments(self, feats_app):
        if self.is_valid():
            segment_names = [
                form.cleaned_data['segment'] for form in self.forms
            ]
            segments = [
                feats_app.segments[segment_name]
                for segment_name in segment_names
            ]
            return segments
        return None


def feature_segment_formset(feature_handle, state=None, data=None):
    class FormsetForm(FeatureSegmentForm):
        def __init__(self, *args, **kwargs):
            super().__init__(feature_handle, *args, **kwargs)
    initial = None
    extra = 1
    if state is not None:
        initial = []
        for segment in state.segments:
            extra = 0
            initial.append({
                'segment': segment.name,
            })

    return formset_factory(
        FormsetForm,
        formset=FeatureSegmentFormset,
        extra=extra,
    )(
        initial=initial,
        data=data,
        prefix='segment'
    )


class FeatureSegmentForm(base.Form):
    """
    Maps a Segment to a feature. Intended to be used in a Formset
    """

    def __init__(self, feature_handle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['segment'] = base.ChoiceField(
            choices=[
                (name, name)
                for name, segment in feature_handle.valid_segments().items()
            ],
            required=True
        )


class SelectorMappingFormset(BaseFormSet):
    def __init__(self, data=None, prefix=None, *args, **kwargs):
        if data is not None:
            data = base.compress_formsets(data, prefix)
        super().__init__(*args, **kwargs, data=data, prefix=prefix)


def selector_mapping_formset(segments, state, data=None):
    class FormsetForm(SelectorMappingForm):
        def __init__(self, *args, **kwargs):
            super().__init__(segments, state.selectors, *args, **kwargs)

    initial = None
    extra = 1
    if state is not None:
        initial = []
        for values, selector in state.selector_mapping.items():
            extra = 0
            segment_values = {}
            for segment, value in zip(state.segments, values):
                segment_values['segment[{}]'.format(segment.name)] = value
            initial.append({
                'segment': segment.name,
                **segment_values,
            })

    return formset_factory(
        FormsetForm,
        formset=SelectorMappingFormset,
        extra=extra
    )(
        data=data,
        initial=initial,
        prefix='selector-mapping'
    )


class SelectorMappingForm(base.Form):
    """
    Maps a selector to the result of segmentation.
    """
    def __init__(self, segments, selectors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selectors = selectors
        self.segments = segments
        self.fields['selector'] = base.ChoiceField(
                choices=[
                    (i, selector.name)
                    for i, selector in enumerate(selectors)
                ],
                required=True
        )
        for segment in segments:
            self.fields['segment[{}]'.format(segment.name)] = base.CharField(required=True)

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


class ChangeMapping(base.TemplateView):
    template_name = "feats/segmentation/change_mapping.html"

    def get_segment_formset(self, feature):
        return feature_segment_formset(feature, data=self.request.GET)

    def get_mapping_formset(self, segments, state, data=None):
        return selector_mapping_formset(segments, state, data=data)

    @property
    def feature(self):
        return self.feats_app.features[self.args[0]]

    def get_context_data(self):
        context = super().get_context_data()
        feature = self.feature
        state = feature.state
        if state is None:
            state = FeatureState.initial(self.request.user.username)

        segments = self.get_segment_formset(feature).validate_and_get_segments(self.feats_app)
        context['feature'] = feature
        context['segment_names'] = [segment.name for segment in segments]
        context['formset'] = self.get_mapping_formset(segments, state)
        return context

    def post(self, request, *args, **kwargs):
        feature = self.feature
        state = feature.state
        segments = self.get_segment_formset(feature).validate_and_get_segments(self.feats_app)
        if state is None:
            state = FeatureState.initial(self.request.user.username)

        mapping_formset = self.get_mapping_formset(segments, state, request.POST)
        if mapping_formset.is_valid():
            selector_mapping = dict(
                form.get_mapping_entry() for form in mapping_formset
            )
            state = FeatureState(
                    segments=segments,
                    selectors=state.selectors,
                    selector_mapping=selector_mapping,
                    created_by=self.request.user.username
            )
            self.feature.state = state
            return HttpResponseRedirect(
                reverse('feats:detail', args=self.args)
            )

        return HttpResponseBadRequest()


class ChangeSegmentation(base.TemplateView):
    """
    Changes how a Feature is Segmented and how selectors map to those segments.

    Updating segmentation resets any selector mappings, so this form is done in
    two steps
    The first form submits through a GET to mapping url with the segments.
        This does not save any data to the database.
    The next form submits through a POST to mapping url with the segments and mappings.
        This creates a new feature state and persists it.

    We update both segmentation and mapping in the same POST, as the alternative
    is to delete all mappings when segmentation is updated.
    """
    template_name = 'feats/segmentation/change_segments.html'

    @property
    def feature(self):
        return self.feats_app.features[self.args[0]]

    def get_formset(self, feature, state):
        return feature_segment_formset(feature, state=state)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature = self.feature
        state = feature.state
        if state is None:
            state = FeatureState.initial(
                    self.request.user.username
            )
        segment_formset = self.get_formset(feature, state)
        context['formset'] = segment_formset
        context['feature'] = feature
        return context

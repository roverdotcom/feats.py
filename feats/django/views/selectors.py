from collections import defaultdict
from django.http import Http404
from django.http.response import HttpResponseBadRequest, HttpResponseRedirect
from django.utils.functional import cached_property
from django.urls import reverse
from feats import selector
from feats.state import FeatureState
from feats.django.views import base
from feats.django.templatetags.feats import selector_type


class SelectorForm(base.Form):
    name = base.CharField(required=True)

    def __init__(self, _type: str, selector=None, initial=None, *args, **kwargs):
        if selector is not None:
            initial = initial or {}
            initial['name'] = selector.name

        super().__init__(initial=initial, *args, **kwargs)
        self.fields['_type'] = base.HiddenCharField(
            required=True,
            initial=_type
        )


class StaticSelectorForm(SelectorForm):
    def __init__(self, feature_handle, selector=None, initial=None, *args, **kwargs):
        if selector is not None:
            initial = initial or {}
            initial['implementation'] = selector.value

        super().__init__('static', selector, initial, *args, **kwargs)
        self.feature_handle = feature_handle
        self.fields['implementation'] = base.ChoiceField(
            choices=[
                (name, name)
                for name in feature_handle.feature.implementations.keys()
            ],
            required=True,
        )

    def create_selector(self):
        return selector.Static.from_data(
            self.feature_handle.app, {
                'value': self.cleaned_data['implementation'],
                'name': self.cleaned_data['name'],
            }
        )


class WeightedSelectorForm(SelectorForm):
    def __init__(self, feature_handle, _type, selector=None, initial=None, *args, **kwargs):
        if selector is not None:
            initial = initial or {}
            for impl_name, weight in selector.weights.items():
                initial['weights[{}]'.format(impl_name)] = weight

        super().__init__(_type, selector, initial, *args, **kwargs)
        self.feature_handle = feature_handle
        for name in feature_handle.feature.implementations.keys():
            key = 'weights[{}]'.format(name)
            self.fields[key] = base.IntegerField(
                label=name,
                required=True,
                min_value=0,
                initial=0,
            )
            self.fields[key].fieldset = 'Weights'

    def get_weights(self):
        weights = {}
        for name in self.feature_handle.feature.implementations.keys():
            weight = self.cleaned_data['weights[{}]'.format(name)]
            weights[name] = weight
        return weights


class RolloutSelectorForm(WeightedSelectorForm):
    def __init__(self, feature_handle, selector=None, initial=None, *args, **kwargs):
        if selector is not None:
            initial = initial or {}
            initial['segment'] = selector.segment.name

        super().__init__(feature_handle, 'rollout', selector, initial, *args, **kwargs)
        self.fields['segment'] = base.ChoiceField(
            choices=[
                (name, name) for name in feature_handle.valid_segments().keys()
            ],
            required=True,
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
    def __init__(self, feature_handle, selector=None, initial=None, *args, **kwargs):
        if selector is not None:
            initial = initial or {}
            initial['segment'] = selector.segment.name

        super().__init__(feature_handle, 'experiment', selector, initial, *args, **kwargs)
        self.fields['segment'] = base.ChoiceField(
            choices=[
                (name, name) for name in feature_handle.valid_segments().keys()
            ],
            required=True,
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


class AddSelector(base.TemplateView):
    template_name = 'feats/add_selector.html'
    forms = {
        'experiment': ExperimentSelectorForm,
        'static': StaticSelectorForm,
        'rollout': RolloutSelectorForm,
    }

    @property
    def feature(self):
        return self.feats_app.features[self.args[0]]

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


class ChangeSelector(base.TemplateView):
    template_name = 'feats/change_selector.html'
    forms = {
            'feats.selector.Static': StaticSelectorForm,
            'feats.selector.Rollout': RolloutSelectorForm,
            'feats.selector.Experiment': ExperimentSelectorForm,
    }

    @cached_property
    def feature(self):
        return self.feats_app.features[self.args[0]]

    @property
    def selector_idx(self):
        return int(self.args[1])

    @cached_property
    def selector(self):
        return self.state.selectors[self.selector_idx]

    @cached_property
    def state(self):
        state = self.feature.get_current_state()
        if state is None:
            raise Http404()
        return state

    @cached_property
    def form(self):
        return self.forms[selector_type(self.selector)]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feature'] = self.feature
        context['form'] = self.form(self.feature, selector=self.selector)
        context['selector'] = self.selector
        return context

    def post(self, request, *args, **kwargs):
        form = self.form(self.feature, data=request.POST, selector=self.selector)
        if form.is_valid():
            if form.has_changed():
                selectors = self.state.selectors.copy()
                selectors[self.selector_idx] = form.create_selector()
                state = FeatureState(
                        segments=self.state.segments,
                        selectors=selectors,
                        selector_mapping=self.state.selector_mapping,
                        created_by=self.request.user.username,
                )
                self.feature.set_state(state)
            return HttpResponseRedirect(
                reverse('feats:detail', args=self.args[:1])
            )
        return HttpResponseBadRequest()

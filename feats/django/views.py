from django import forms
from django.apps import apps
from django.http.response import HttpResponseRedirect
from django.http.response import HttpResponseBadRequest
from django.urls import reverse
from django.views.generic.base import TemplateView

app_config = apps.get_app_config('feats')


class Index(TemplateView):
    template_name = 'feats/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = app_config.feats_app.features.values()
        return context


class Detail(TemplateView):
    template_name = 'feats/detail.html'

    @property
    def feature(self):
        return app_config.feats_app.features[self.args[0]]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feature'] = self.feature
        return context


class ChangeSegmentation(TemplateView):
    template_name = 'feats/change_segmentation.html'

    @property
    def feature(self):
        return app_config.feats_app.features[self.args[0]]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feature'] = self.feature
        return context


class AddStaticForm(forms.BaseForm):
    def create_selector(self):
        print("Create Static")


class AddRolloutForm(forms.BaseForm):
    def create_selector(self):
        print("Create Rollout")


class AddExperimentForm(forms.Form):
    def create_selector(self):
        print("Create Experiment")


class AddSelector(TemplateView):
    template_name = 'feats/add_selector.html'
    forms = {
        'experiment': AddExperimentForm,
        'static': AddStaticForm,
        'rollout': AddRolloutForm,
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
        class Static(AddStaticForm):
            base_fields = {
                '_type': forms.CharField(
                    required=True,
                    widget=forms.HiddenInput,
                    initial='static'
                )
            }

        class Rollout(AddRolloutForm):
            base_fields = {
                '_type': forms.CharField(
                    required=True,
                    widget=forms.HiddenInput,
                    initial='rollout'
                )
            }

        class Experiment(AddExperimentForm):
            base_fields = {
                '_type': forms.CharField(
                    required=True,
                    widget=forms.HiddenInput,
                    initial='experiment'
                )
            }

        base_fields = {}
        choices = []
        for name in self.feature.feature.implementations.keys():
            base_fields['{}_weight'.format(name)] = forms.IntegerField(
                required=True,
                min_value=0,
                initial=0,
            )
            choices.append((name, name))
        Rollout.base_fields.update(base_fields)
        Experiment.base_fields.update(base_fields)
        Static.base_fields['value'] = forms.ChoiceField(
            choices=choices,
            required=True
        )

        form_classes = {
            'rollout': Rollout,
            'experiment': Experiment,
            'static': Static,
        }
        init_forms = {}
        if self.request.method == 'POST':
            _type = self.request.POST['_type']
            form_to_bind = form_classes[_type]
            del form_classes[_type]
            init_forms[_type] = form_to_bind(self.request.POST)

        for key, form in form_classes.items():
            init_forms[key] = form()
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

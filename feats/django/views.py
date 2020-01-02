from django.views.generic.base import TemplateView
from django.apps import apps

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


class AddSelector(TemplateView):
    template_name = 'feats/add_selector.html'

    @property
    def feature(self):
        return app_config.feats_app.features[self.args[0]]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feature'] = self.feature
        return context


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

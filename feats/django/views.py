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
        print(self.feature)
        context['feature'] = self.feature
        return context


class Change(TemplateView):
    template_name = 'feats/change.html'

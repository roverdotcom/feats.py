from django.shortcuts import render
from django.views import View
from django.views.generic.base import TemplateView
from django.apps import apps

class Index(TemplateView):
    template_name = 'feats/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = apps.get_app_config('feats').feats_app.features
        return context


class Detail(View):
    template_name = 'feats/detail.html'

    def get(self, request):
        return render(request, self.template_name)


class Change(View):
    template_name = 'feats/change.html'

    def get(self, request):
        return render(request, self.template_name)

    def update(self, request):
        raise ValueError()

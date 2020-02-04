from .base import TemplateView


class Detail(TemplateView):
    template_name = 'feats/detail.html'

    @property
    def feature(self):
        return self.feats_app.features[self.args[0]]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature = self.feature
        state = feature.get_current_state()
        context['feature'] = feature
        context['state'] = state
        if state:
            context['segment_names'] = [
                segment.name for segment in state.segments
            ]
        return context

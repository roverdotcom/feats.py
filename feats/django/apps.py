from django.apps import AppConfig
from feats import App
from feats.storage import Memory

feats = App(storage=Memory())

class FeatsConfig(AppConfig):
    name = 'feats.django'
    label = 'feats'

    @property
    def feats_app(self):
        return feats

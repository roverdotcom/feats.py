from django.apps import AppConfig
from feats.django.apps import FeatsConfig as Base
from feats import App
from feats.storage import Memory

feats = App(storage=Memory())

class FeatsConfig(Base):
    @property
    def feats_app(self):
        return feats

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady
from django.conf import settings
from feats import App


class FeatsConfig(AppConfig):
    name = 'feats.django'
    label = 'feats'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._feats_app = None

    def ready(self):
        feats_app = settings.FEATS
        if feats_app is None:
            raise ImproperlyConfigured(
                "The setting FEATS was not set. It must be set to a feats.App"
            )
        if not isinstance(feats_app, App):
            raise ImproperlyConfigured(
                "The setting FEATS must be a feats.App, was {}",
                type(feats_app)
            )
        self._feats_app = feats_app

    @property
    def feats_app(self):
        if self._feats_app is None:
            raise AppRegistryNotReady(
                "Cannot use the Feats AppConfig until Django has been initialized"
            )
        return self._feats_app

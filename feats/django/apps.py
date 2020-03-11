from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady
from django.conf import settings
from feats import App
from importlib import import_module


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
        # Register other feats files in other django apps
        for app in self.apps.get_app_configs():
            try:
                import_module('.feats', app.name)
            except ModuleNotFoundError:
                # Not all apps need to have feats
                pass

    @property
    def feats_app(self):
        if self._feats_app is None:
            raise AppRegistryNotReady(
                "Cannot use the Feats AppConfig until Django has been initialized"
            )
        return self._feats_app

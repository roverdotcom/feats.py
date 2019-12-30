from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady
from django.conf import settings
from feats import App


class FeatsConfig(AppConfig):
    name = 'feats.django'
    label = 'feats'

    def ready(self):
        self.feats_app = settings.get('FEATS')
        if self.feats_app is None:
            raise ImproperlyConfigured(
                "The setting FEATS was not set. It must be set to a feats.App"
            )
        if not isinstance(self.feats_app, App):
            raise ImproperlyConfigured(
                "The setting FEATS must be a feats.App, was {}",
                type(self.feats_app)
            )

    @property
    def feats_app(self):
        # Overwritten in ready(). Not allowed to use this until the app is
        # configured
        raise AppRegistryNotReady(
            "Cannot use the Feats AppConfig until Django has been initialized"
        )

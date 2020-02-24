import django
from django.conf import settings
from example.project import settings as project_settings
import feats
from feats.storage import Memory

if not settings.configured:
    settings.configure(INSTALLED_APPS=['feats.django'], FEATS=feats.App(storage=Memory()))
    django.setup()

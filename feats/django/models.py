from django.db import models


class FeatsAccess(models.Model):
    """
    Fake Model, Exists only for the content-type required for permissions
    """
    class Meta:
        managed = False

from django.db import models

from common.managers import BaseManager


class BaseModel(models.Model):
    objects = BaseManager()

    class Meta:
        abstract = True

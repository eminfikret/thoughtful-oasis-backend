from django.db import models

from common.query_sets import BaseQuerySet


class BaseManager(models.Manager):
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)

    def filter_optional(self, *args, **kwargs):
        return self.get_queryset().filter_optional(*args, **kwargs)

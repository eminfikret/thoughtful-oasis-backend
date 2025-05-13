from dirtyfields import DirtyFieldsMixin
from django.contrib.auth.models import User
from django.db import models

from common.models import BaseModel


class Channel(DirtyFieldsMixin, BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='channels',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'channels'
        ordering = ['-created_at', '-updated_at']
        verbose_name = 'Channel'
        verbose_name_plural = 'Channels'
        get_latest_by = 'created_at'

    def __str__(self):
        return self.name

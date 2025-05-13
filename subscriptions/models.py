from django.contrib.auth.models import User
from django.db import models

from channels.models import Channel
from common.models import BaseModel


class Subscription(BaseModel):
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        null=False,
        blank=False,
    )
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        null=False,
        blank=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscriptions'
        unique_together = ('channel', 'subscriber')
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        get_latest_by = 'created_at'

    def __str__(self):
        return f"{self.subscriber} subscribed to '{self.channel.name}' on {self.created_at}"

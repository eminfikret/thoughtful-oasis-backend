from django.db import models
from django.contrib.auth.models import User
from channels.models import Channel

class Post(models.Model):
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        ordering = ['created_at', 'updated_at']
        verbose_name = 'Channel'
        verbose_name_plural = 'Channels'
        get_latest_by = 'created_at'

    def __str__(self):
        return self.title
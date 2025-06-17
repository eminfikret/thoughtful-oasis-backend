from typing import List, Optional

from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramSimilarity

from channels.models import Channel
from channels.types import ChannelId
from common.params import PaginationParams


class ChannelRepository:
    @staticmethod
    def get_channels(
            search: Optional[str] = None,
            pagination: Optional[PaginationParams] = None,
    ) -> List[Channel]:
        pagination = pagination or PaginationParams()
        queryset = Channel.objects.all()

        if search:
            queryset = queryset.annotate(
                similarity=TrigramSimilarity('name', search) + 
                          TrigramSimilarity('description', search)
            ).filter(similarity__gt=0.1).order_by('-similarity')
        
        return list(queryset[pagination.offset:pagination.offset + pagination.limit])

    @staticmethod
    def get_channels_count(search: Optional[str] = None) -> int:
        queryset = Channel.objects.all()

        if search:
            queryset = queryset.annotate(
                similarity=TrigramSimilarity('name', search) + 
                          TrigramSimilarity('description', search)
            ).filter(similarity__gt=0.1)

        return queryset.count()

    @staticmethod
    def get_channel_by_id(channel_id: ChannelId) -> Optional[Channel]:
        return Channel.objects.filter(id=channel_id).first()

    @staticmethod
    def create_channel(
            name: str,
            description: str,
            slug: str,
            owner: User
    ) -> Channel:
        return Channel.objects.create(
            name=name,
            description=description,
            slug=slug,
            owner=owner
        )

    @staticmethod
    def update_channel(channel: Channel) -> Channel:
        channel.save()
        return channel

    @staticmethod
    def name_exists(name: str) -> bool:
        return Channel.objects.filter(name__iexact=name).exists()

    @staticmethod
    def delete_channel(channel: Channel) -> None:
        channel.delete()
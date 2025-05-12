from typing import List, Optional

from django.contrib.auth.models import User
from django.db.models import Q

from channels.models import Channel
from channels.params import ChannelsParams
from channels.types import ChannelId


class ChannelRepository:
    @staticmethod
    def get_channels(params: ChannelsParams) -> List[Channel]:
        queryset = Channel.objects.all()

        if params.search:
            queryset = queryset.filter(
                Q(name__icontains=params.search) | Q(description__icontains=params.search)
            )

        return list(queryset[params.offset:params.offset + params.limit])

    @staticmethod
    def get_channels_count(search: Optional[str] = None) -> int:
        queryset = Channel.objects.all()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
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
    def slug_exists(slug: str) -> bool:
        return Channel.objects.filter(slug=slug).exists()

    @staticmethod
    def delete_channel(channel: Channel) -> None:
        channel.delete()
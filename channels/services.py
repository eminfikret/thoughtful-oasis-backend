from typing import List, Optional

from django.contrib.auth.models import User
from django.utils.text import slugify


from channels.exceptions import ChannelNotFound
from channels.models import Channel
from channels.repositories import ChannelRepository
from channels.types import ChannelId


class ChannelService:
    @staticmethod
    def get_all_channels() -> List[Channel]:
        return ChannelRepository.get_all_channels()

    @staticmethod
    def get_channel_by_id(channel_id: ChannelId) -> Channel:
        """
        Raises:
            ChannelNotFound: if no channel exists with the given ID.
        """
        channel = ChannelRepository.get_channel_by_id(channel_id)
        if channel is None:
            raise ChannelNotFound(channel_id)

        return channel

    @staticmethod
    def create_channel(
            name: str,
            description: str,
            owner: User
    ) -> Channel:
        slug = ChannelService._generate_unique_slug(name)
        return ChannelRepository.create_channel(name, description, slug, owner)

    @staticmethod
    def update_channel(
            channel_id: ChannelId,
            name: Optional[str] = None,
            description: Optional[str] = None
    ) -> Channel:
        channel = ChannelService.get_channel_by_id(channel_id)

        updated_fields = {}

        if name is not None and name != channel.name:
            updated_fields['name'] = name
            updated_fields['slug'] = ChannelService._generate_unique_slug(name)

        if description is not None and description != channel.description:
            updated_fields['description'] = description

        if updated_fields:
            for field, value in updated_fields.items():
                setattr(channel, field, value)
            return ChannelRepository.update_channel(channel)

        return channel

    @staticmethod
    def _generate_unique_slug(name: str) -> str:
        base_slug = slugify(name)
        slug = base_slug

        counter = 1
        while ChannelRepository.slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    @staticmethod
    def delete_channel(channel_id: ChannelId) -> None:
        """
        Raises:
            ChannelNotFound: if no channel exists with the given ID.
        """
        channel = ChannelService.get_channel_by_id(channel_id)
        ChannelRepository.delete_channel(channel)

from typing import List, Optional

from django.contrib.auth.models import User
from django.utils.text import slugify

from channels.dtos import CreateChannelDto, UpdateChannelDto
from channels.exceptions import ChannelNotFoundException, UnauthorizedChannelAccessException
from channels.models import Channel
from channels.repositories import ChannelRepository
from channels.types import ChannelId
from common.params import PaginationParams


class ChannelService:
    @staticmethod
    def get_channels(
            search: Optional[str] = None,
            pagination: Optional[PaginationParams] = None,
    ) -> List[Channel]:
        pagination = pagination or PaginationParams()

        return ChannelRepository.get_channels(
            search=search,
            pagination=pagination,
        )

    @staticmethod
    def get_channels_count(search: Optional[str] = None) -> int:
        return ChannelRepository.get_channels_count(search)

    @staticmethod
    def get_channel_by_id(channel_id: ChannelId) -> Channel:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
        """
        channel = ChannelRepository.get_channel_by_id(channel_id)
        if channel is None:
            raise ChannelNotFoundException(channel_id)
        return channel

    @staticmethod
    def create_channel(
        dto: CreateChannelDto,
        owner: User,
    ) -> Channel:
        slug = ChannelService._generate_unique_slug(dto.name)
        return ChannelRepository.create_channel(dto.name, dto.description, slug, owner)

    @staticmethod
    def update_channel(
        channel_id: ChannelId,
        dto: UpdateChannelDto,
        requester: User,
    ) -> Channel:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
            UnauthorizedChannelAccessException: If the requester is neither the owner nor an admin.
        """
        channel = ChannelService.get_channel_by_id(channel_id)

        if not (channel.owner == requester or requester.is_staff):
            raise UnauthorizedChannelAccessException()

        if dto.name is not None:
            channel.name = dto.name
        if dto.description is not None:
            channel.description = dto.description

        if 'name' in channel.get_dirty_fields():
            channel.slug = ChannelService._generate_unique_slug(dto.name)

        if channel.is_dirty():
            return ChannelRepository.update_channel(channel)

        return channel

    @staticmethod
    def delete_channel(
        channel_id: ChannelId,
        requester: User,
    ) -> None:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
            UnauthorizedChannelAccessException: If the requester is neither the owner nor an admin.
        """
        channel = ChannelService.get_channel_by_id(channel_id)

        if not (channel.owner == requester or requester.is_staff):
            raise UnauthorizedChannelAccessException()

        ChannelRepository.delete_channel(channel)

    @staticmethod
    def _generate_unique_slug(name: str) -> str:
        base_slug = slugify(name)
        slug = base_slug

        counter = 1
        while ChannelRepository.slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug


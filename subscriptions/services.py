from typing import List, Optional

from django.contrib.auth.models import User

from channels.services import ChannelService
from channels.types import ChannelId
from common.params import PaginationParams
from subscriptions.exceptions import UnauthorizedSubscriptionAccessException
from subscriptions.models import Subscription
from subscriptions.repositories import SubscriptionRepository


class SubscriptionService:
    @staticmethod
    def get_subscriptions_by_channel(
            channel_id: ChannelId,
            requester: User,
            pagination: Optional[PaginationParams] = None,
    ) -> List[Subscription]:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
            UnauthorizedSubscriptionAccessException:
                If the requester is neither the owner nor an admin.
        """
        pagination = pagination or PaginationParams()

        channel = ChannelService.get_channel_by_id(channel_id)
        if not (channel.owner == requester or requester.is_staff):
            raise UnauthorizedSubscriptionAccessException()

        return SubscriptionRepository.get_subscriptions(
            channel=channel,
            pagination=pagination
        )

    @staticmethod
    def get_subscriptions_by_subscriber(
            subscriber: User,
            requester: User,
            pagination: Optional[PaginationParams] = None,
    ) -> List[Subscription]:
        """
        Raises:
            UnauthorizedSubscriptionAccessException:
                If the requester is neither the subscriber nor an admin.
        """
        pagination = pagination or PaginationParams()

        if subscriber != requester and not requester.is_staff:
            raise UnauthorizedSubscriptionAccessException()

        return SubscriptionRepository.get_subscriptions(
            subscriber=subscriber,
            pagination=pagination
        )

    @staticmethod
    def get_subscriptions_count_by_channel(channel_id: ChannelId, requester: User) -> int:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
            UnauthorizedSubscriptionAccessException:
                If the requester is neither the owner nor an admin.
        """
        channel = ChannelService.get_channel_by_id(channel_id)

        if not (channel.owner == requester or requester.is_staff):
            raise UnauthorizedSubscriptionAccessException()

        return SubscriptionRepository.get_subscriptions_count(channel=channel)

    @staticmethod
    def get_subscriptions_count_by_subscriber(subscriber: User, requester: User) -> int:
        """
        Raises:
            UnauthorizedSubscriptionAccessException:
                If the requester is neither the subscriber nor an admin.
        """
        if subscriber != requester and not requester.is_staff:
            raise UnauthorizedSubscriptionAccessException()

        return SubscriptionRepository.get_subscriptions_count(subscriber=subscriber)

    @staticmethod
    def subscribe(channel_id: ChannelId, subscriber: User) -> None:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
        """
        channel = ChannelService.get_channel_by_id(channel_id)
        if not SubscriptionRepository.get_subscription(channel, subscriber):
            SubscriptionRepository.create_subscription(channel, subscriber)

    @staticmethod
    def unsubscribe(channel_id: ChannelId, subscriber: User) -> None:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
        """
        channel = ChannelService.get_channel_by_id(channel_id)
        subscription = SubscriptionRepository.get_subscription(channel, subscriber)
        if subscription:
            SubscriptionRepository.delete_subscription(subscription)




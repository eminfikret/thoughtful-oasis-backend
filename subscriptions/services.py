from typing import List, Optional

from django.contrib.auth.models import User

from channels.services import ChannelService
from channels.types import ChannelId
from common.params import PaginationParams
from subscriptions.exceptions import SubscriptionPermissionDeniedException
from subscriptions.models import Subscription
from subscriptions.repositories import SubscriptionRepository
from users.exceptions import UserNotFoundException
from users.services import UserService
from users.types import UserId


class SubscriptionService:
    @staticmethod
    def get_subscriptions_by_channel_id(
            channel_id: ChannelId,
            requester: User,
            pagination: Optional[PaginationParams] = None,
    ) -> List[Subscription]:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
            SubscriptionPermissionDeniedException:
                If the requester is neither the owner nor an admin.
        """
        pagination = pagination or PaginationParams()

        channel = ChannelService.get_channel_by_id(channel_id)
        if not (channel.owner == requester or requester.is_staff):
            raise SubscriptionPermissionDeniedException()

        return SubscriptionRepository.get_subscriptions(
            channel=channel,
            pagination=pagination
        )

    @staticmethod
    def get_subscriptions_by_user_id(
            user_id: UserId,
            requester: User,
            pagination: Optional[PaginationParams] = None,
    ) -> List[Subscription]:
        """
        Raises:
            UserNotFoundException: if no user exists with the given ID.
            SubscriptionPermissionDeniedException:
                If the requester is neither the subscriber nor an admin.
        """
        pagination = pagination or PaginationParams()

        subscriber = UserService().get_user_by_id(user_id)
        if not subscriber:
            raise UserNotFoundException(user_id)

        if subscriber != requester and not requester.is_staff:
            raise SubscriptionPermissionDeniedException()

        return SubscriptionRepository.get_subscriptions(
            subscriber=subscriber,
            pagination=pagination
        )

    @staticmethod
    def get_subscriptions_count_by_channel_id(channel_id: ChannelId, requester: User) -> int:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
            SubscriptionPermissionDeniedException:
                If the requester is neither the owner nor an admin.
        """
        channel = ChannelService.get_channel_by_id(channel_id)

        if not (channel.owner == requester or requester.is_staff):
            raise SubscriptionPermissionDeniedException()

        return SubscriptionRepository.get_subscriptions_count(channel=channel)

    @staticmethod
    def get_subscriptions_count_by_user_id(user_id: UserId, requester: User) -> int:
        """
        Raises:
            UserNotFoundException: if no user exists with the given ID.
            SubscriptionPermissionDeniedException:
                If the requester is neither the subscriber nor an admin.
        """
        subscriber = UserService().get_user_by_id(user_id)
        if not subscriber:
            raise UserNotFoundException(user_id)

        if subscriber != requester and not requester.is_staff:
            raise SubscriptionPermissionDeniedException()

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

    @staticmethod
    def is_subscribed(channel_id: ChannelId, user: User) -> bool:
        """
        Check if a user is subscribed to a channel.

        Args:
            channel_id: ID of the channel
            user: User to check subscription for

        Returns:
            True if the user is subscribed, False otherwise

        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
        """
        channel = ChannelService.get_channel_by_id(channel_id)
        return SubscriptionRepository.get_subscription(channel, user) is not None




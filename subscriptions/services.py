from typing import List, Optional

from django.contrib.auth.models import User

from channels.services import ChannelService
from channels.types import ChannelId
from subscriptions.exceptions import UnauthorizedSubscriptionAccessException
from subscriptions.models import Subscription
from subscriptions.params import SubscriptionsParams
from subscriptions.repositories import SubscriptionRepository


class SubscriptionService:
    @staticmethod
    def get_subscriptions_by_channel(
            channel_id: ChannelId,
            params: SubscriptionsParams,
            user: User
    ) -> List[Subscription]:
        """
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
            UnauthorizedSubscriptionAccessException: If the user is neither the owner nor an admin.
        """
        channel = ChannelService.get_channel_by_id(channel_id)
        if not (channel.owner == user or user.is_staff):
            raise UnauthorizedSubscriptionAccessException()
        return SubscriptionRepository.get_subscriptions_by_channel(channel, params)

    @staticmethod
    def get_subscriptions_by_subscriber(
            subscriber: User,
            params: SubscriptionsParams,
    ) -> List[Subscription]:
        return SubscriptionRepository.get_subscriptions_by_subscriber(subscriber, params)

    @staticmethod
    def get_subscriptions_count(subscriber: Optional[User] = None) -> int:
        return SubscriptionRepository.get_subscriptions_count(subscriber)

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




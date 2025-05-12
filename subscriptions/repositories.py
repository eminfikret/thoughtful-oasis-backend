from typing import List, Optional

from django.contrib.auth.models import User

from channels.models import Channel
from common.params import PaginationParams
from subscriptions.models import Subscription


class SubscriptionRepository:
    @staticmethod
    def get_subscription(
            channel: Channel,
            subscriber: User
    ) -> Optional[Subscription]:
        return Subscription.objects.filter(channel=channel, subscriber=subscriber).first()

    @staticmethod
    def get_subscriptions(
            channel: Optional[Channel] = None,
            subscriber: Optional[User] = None,
            pagination: Optional[PaginationParams] = None,
    ) -> List[Subscription]:
        pagination = pagination or PaginationParams()

        queryset =  Subscription.objects.filter_optional(
            channel=channel,
            subscriber=subscriber
        )

        return list(queryset[pagination.offset:pagination.offset + pagination.limit])

    @staticmethod
    def get_subscriptions_count(
            channel: Optional[Channel] = None,
            subscriber: Optional[User] = None,
    ) -> int:
        return Subscription.objects.filter_optional(
            channel=channel,
            subscriber=subscriber,
        ).count()

    @staticmethod
    def create_subscription(channel: Channel, subscriber: User) -> Subscription:
        return Subscription.objects.create(channel=channel, subscriber=subscriber)

    @staticmethod
    def delete_subscription(subscription: Subscription) -> None:
        subscription.delete()


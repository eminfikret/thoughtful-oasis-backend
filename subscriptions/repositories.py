from typing import List, Optional

from django.contrib.auth.models import User

from channels.models import Channel
from subscriptions.models import Subscription
from subscriptions.params import SubscriptionsParams


class SubscriptionRepository:
    @staticmethod
    def get_subscription(channel: Channel, subscriber: User) -> Optional[Subscription]:
        return Subscription.objects.filter(channel=channel, subscriber=subscriber).first()

    @staticmethod
    def get_subscriptions_by_channel(
            channel: Channel,
            params: SubscriptionsParams,
    ) -> List[Subscription]:
        queryset =  Subscription.objects.filter(channel=channel)
        return list(queryset[params.offset:params.offset + params.limit])

    @staticmethod
    def get_subscriptions_by_subscriber(
            subscriber: User,
            params: SubscriptionsParams,
    ) -> List[Subscription]:
        queryset =  Subscription.objects.filter(subscriber=subscriber)
        return list(queryset[params.offset:params.offset + params.limit])

    @staticmethod
    def get_subscriptions_count(subscriber: Optional[User] = None) -> int:
        if subscriber is not None:
            return Subscription.objects.filter(subscriber=subscriber).count()
        return Subscription.objects.count()

    @staticmethod
    def create_subscription(channel: Channel, subscriber: User) -> Subscription:
        return Subscription.objects.create(channel=channel, subscriber=subscriber)

    @staticmethod
    def delete_subscription(subscription: Subscription) -> None:
        subscription.delete()


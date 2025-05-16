from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from common.params import PaginationParams
from subscriptions.models import Subscription
from subscriptions.repositories import SubscriptionRepository


class SubscriptionRepositoryTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='o@example.com',
            password='pass'
        )
        self.subscriber = User.objects.create_user(
            username='sub',
            email='s@example.com',
            password='pass'
        )
        self.other = User.objects.create_user(
            username='other',
            email='x@example.com',
            password='pass'
        )

        self.channel = Channel.objects.create(
            name='Test Channel',
            description='desc',
            slug='test-channel',
            owner=self.owner
        )

        self.subscription = Subscription.objects.create(
            channel=self.channel,
            subscriber=self.subscriber
        )

    def test_get_subscriptions_by_channel(self):
        results = SubscriptionRepository.get_subscriptions(channel=self.channel)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.subscription)

    def test_get_subscriptions_by_subscriber(self):
        results = SubscriptionRepository.get_subscriptions(subscriber=self.subscriber)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.subscription)

    def test_get_subscriptions_pagination(self):
        for i in range(5):
            user = User.objects.create_user(username=f'user{i}', email=f'u{i}@x.com', password='p')
            Subscription.objects.create(channel=self.channel, subscriber=user)

        pagination = PaginationParams(limit=3, offset=1)
        results = SubscriptionRepository.get_subscriptions(
            channel=self.channel,
            pagination=pagination
        )

        self.assertEqual(len(results), 3)

    def test_get_subscriptions_count_by_channel(self):
        count = SubscriptionRepository.get_subscriptions_count(channel=self.channel)
        self.assertEqual(count, 1)

    def test_get_subscriptions_count_by_subscriber(self):
        count = SubscriptionRepository.get_subscriptions_count(subscriber=self.subscriber)
        self.assertEqual(count, 1)

    def test_get_subscription_existing(self):
        result = SubscriptionRepository.get_subscription(
            channel=self.channel,
            subscriber=self.subscriber
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.subscriber, self.subscriber)

    def test_get_subscription_none(self):
        result = SubscriptionRepository.get_subscription(
            channel=self.channel,
            subscriber=self.other
        )

        self.assertIsNone(result)

    def test_create_subscription(self):
        SubscriptionRepository.create_subscription(self.channel, self.other)
        self.assertEqual(Subscription.objects.count(), 2)

    def test_delete_subscription(self):
        SubscriptionRepository.delete_subscription(self.subscription)
        self.assertFalse(Subscription.objects.filter(id=self.subscription.id).exists())

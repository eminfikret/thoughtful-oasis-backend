from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from subscriptions.models import Subscription


class SubscriptionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            email='u@example.com',
            password='pass'
        )

        self.channel = Channel.objects.create(
            name='Test Channel',
            slug='test-channel',
            description='desc',
            owner=self.user
        )

    def test_subscription_creation(self):
        subscription = Subscription.objects.create(subscriber=self.user, channel=self.channel)
        self.assertEqual(subscription.subscriber, self.user)
        self.assertEqual(subscription.channel, self.channel)
        self.assertIsNotNone(subscription.created_at)

    def test_subscription_str(self):
        subscription = Subscription.objects.create(subscriber=self.user, channel=self.channel)
        expected = f"{self.user} subscribed to '{self.channel.name}' on {subscription.created_at}"
        self.assertEqual(str(subscription), expected)

    def test_unique_together_constraint(self):
        Subscription.objects.create(subscriber=self.user, channel=self.channel)
        with self.assertRaises(Exception):
            Subscription.objects.create(subscriber=self.user, channel=self.channel)
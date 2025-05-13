from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from subscriptions.models import Subscription
from subscriptions.serializers import (
    SubscriberSerializer,
    SubscriptionRawSerializer,
    SubscriptionSerializer,
)


class SubscriptionSerializersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='pass'
        )

        self.channel = Channel.objects.create(
            name='Channel',
            slug='channel',
            description='desc',
            owner=self.user
        )

        self.subscription = Subscription.objects.create(
            channel=self.channel,
            subscriber=self.user
        )

    def test_subscription_raw_serializer(self):
        serializer = SubscriptionRawSerializer(self.subscription)
        data = serializer.data

        self.assertEqual(data['channel_id'], self.channel.id)
        self.assertEqual(data['subscriber_id'], self.user.id)
        self.assertIn('created_at', data)

    def test_subscriber_serializer(self):
        serializer = SubscriberSerializer(self.subscription)
        data = serializer.data

        self.assertEqual(data['id'], self.subscription.id)
        self.assertEqual(data['subscriber']['id'], self.user.id)
        self.assertEqual(data['subscriber']['username'], self.user.username)
        self.assertIn('subscribed_at', data)

    def test_subscription_serializer(self):
        serializer = SubscriptionSerializer(self.subscription)
        data = serializer.data

        self.assertEqual(data['id'], self.subscription.id)
        self.assertEqual(data['channel']['id'], self.channel.id)
        self.assertEqual(data['channel']['name'], self.channel.name)
        self.assertIn('subscribed_at', data)

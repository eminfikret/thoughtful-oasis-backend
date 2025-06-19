from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from channels.types import ChannelId
from subscriptions.exceptions import SubscriptionPermissionDeniedException
from subscriptions.models import Subscription
from subscriptions.services import SubscriptionService
from users.exceptions import UserNotFoundException
from users.types import UserId


class SubscriptionServiceTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='pass'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='pass'
        )
        self.subscriber = User.objects.create_user(
            username='subscriber',
            email='sub@test.com',
            password='pass'
        )
        self.other = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='pass'
        )

        self.channel = Channel.objects.create(
            name='Test Channel',
            description='desc',
            slug='test-channel',
            owner=self.owner
        )

    def test_get_subscriptions_by_channel_as_owner(self):
        SubscriptionService.subscribe(self.channel.id, self.subscriber)

        subs = SubscriptionService.get_subscriptions_by_channel_id(
            channel_id=self.channel.id,
            requester=self.owner
        )

        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0].subscriber, self.subscriber)

    def test_get_subscriptions_by_channel_as_admin(self):
        SubscriptionService.subscribe(self.channel.id, self.subscriber)

        subs = SubscriptionService.get_subscriptions_by_channel_id(
            channel_id=self.channel.id,
            requester=self.admin
        )

        self.assertEqual(len(subs), 1)

    def test_get_subscriptions_by_channel_forbidden(self):
        with self.assertRaises(SubscriptionPermissionDeniedException):
            SubscriptionService.get_subscriptions_by_channel_id(
                channel_id=self.channel.id,
                requester=self.other
            )

    def test_get_subscriptions_by_user_as_self(self):
        SubscriptionService.subscribe(self.channel.id, self.subscriber)

        subs = SubscriptionService.get_subscriptions_by_user_id(
            user_id=self.subscriber.id,
            requester=self.subscriber
        )

        self.assertEqual(len(subs), 1)

    def test_get_subscriptions_by_user_as_admin(self):
        SubscriptionService.subscribe(self.channel.id, self.subscriber)

        subs = SubscriptionService.get_subscriptions_by_user_id(
            user_id=self.subscriber.id,
            requester=self.admin
        )

        self.assertEqual(len(subs), 1)

    def test_get_subscriptions_by_user_forbidden(self):
        with self.assertRaises(SubscriptionPermissionDeniedException):
            SubscriptionService.get_subscriptions_by_user_id(
                user_id=self.subscriber.id,
                requester=self.other
            )

    def test_get_subscriptions_by_user_not_found(self):
        with self.assertRaises(UserNotFoundException):
            SubscriptionService.get_subscriptions_by_user_id(
                user_id=UserId(9999),
                requester=self.admin
            )

    def test_count_subscriptions_by_channel(self):
        SubscriptionService.subscribe(self.channel.id, self.subscriber)

        count = SubscriptionService.get_subscriptions_count_by_channel_id(
            channel_id=self.channel.id,
            requester=self.owner
        )

        self.assertEqual(count, 1)

    def test_count_subscriptions_by_user(self):
        SubscriptionService.subscribe(self.channel.id, self.subscriber)

        count = SubscriptionService.get_subscriptions_count_by_user_id(
            user_id=self.subscriber.id,
            requester=self.subscriber
        )

        self.assertEqual(count, 1)

    def test_subscribe_and_unsubscribe_flow(self):
        SubscriptionService.subscribe(self.channel.id, self.subscriber)
        self.assertEqual(Subscription.objects.count(), 1)

        SubscriptionService.subscribe(self.channel.id, self.subscriber)
        self.assertEqual(Subscription.objects.count(), 1)

        SubscriptionService.unsubscribe(self.channel.id, self.subscriber)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_is_subscribed_returns_true_when_subscribed(self):
        """Test that is_subscribed returns True when the user is subscribed"""
        SubscriptionService.subscribe(self.channel.id, self.subscriber)

        is_subbed = SubscriptionService.is_subscribed(self.channel.id, self.subscriber)
        self.assertTrue(is_subbed)

    def test_is_subscribed_returns_false_when_not_subscribed(self):
        """Test that is_subscribed returns False when the user is not subscribed"""
        is_subbed = SubscriptionService.is_subscribed(self.channel.id, self.other)
        self.assertFalse(is_subbed)

    def test_is_subscribed_raises_exception_for_nonexistent_channel(self):
        """Test that is_subscribed raises an exception for a nonexistent channel"""
        from channels.exceptions import ChannelNotFoundException

        with self.assertRaises(ChannelNotFoundException):
            SubscriptionService.is_subscribed(ChannelId(99999), self.subscriber)

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from channels.models import Channel
from subscriptions.models import Subscription


class SubscriptionControllerTest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.admin = User.objects.create_superuser(username='admin', password='pass123')
        self.subscriber = User.objects.create_user(username='subscriber', password='pass123')
        self.other_user = User.objects.create_user(username='other', password='pass123')

        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Testing',
            slug='test-channel',
            owner=self.owner
        )

        self.client = APIClient()

    def authenticate(self, user: User):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_subscribe_to_channel(self):
        self.authenticate(self.subscriber)
        url = reverse('channel-subscribe', args=[self.channel.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(
            Subscription.objects.filter(subscriber=self.subscriber, channel=self.channel).exists()
        )

    def test_subscribe_invalid_channel(self):
        self.authenticate(self.subscriber)

        url = reverse('channel-subscribe', args=[99999])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unsubscribe_from_channel(self):
        Subscription.objects.create(subscriber=self.subscriber, channel=self.channel)
        self.authenticate(self.subscriber)

        url = reverse('channel-unsubscribe', args=[self.channel.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Subscription.objects.filter(subscriber=self.subscriber, channel=self.channel).exists()
        )

    def test_list_channel_subscribers_as_owner(self):
        Subscription.objects.create(subscriber=self.subscriber, channel=self.channel)
        Subscription.objects.create(subscriber=self.other_user, channel=self.channel)

        self.authenticate(self.owner)

        url = reverse('channel-subscribers', args=[self.channel.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_channel_subscribers_as_admin(self):
        Subscription.objects.create(subscriber=self.subscriber, channel=self.channel)

        self.authenticate(self.admin)

        url = reverse('channel-subscribers', args=[self.channel.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_channel_subscribers_forbidden(self):
        Subscription.objects.create(subscriber=self.subscriber, channel=self.channel)

        self.authenticate(self.other_user)

        url = reverse('channel-subscribers', args=[self.channel.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_user_subscriptions_as_self(self):
        Subscription.objects.create(subscriber=self.subscriber, channel=self.channel)

        self.authenticate(self.subscriber)

        url = reverse('user-subscriptions', args=[self.subscriber.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_user_subscriptions_as_admin(self):
        Subscription.objects.create(subscriber=self.subscriber, channel=self.channel)

        self.authenticate(self.admin)

        url = reverse('user-subscriptions', args=[self.subscriber.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_user_subscriptions_forbidden(self):
        Subscription.objects.create(subscriber=self.subscriber, channel=self.channel)

        self.authenticate(self.other_user)

        url = reverse('user-subscriptions', args=[self.subscriber.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_user_subscriptions_user_not_found(self):
        self.authenticate(self.admin)

        url = reverse('user-subscriptions', args=[99999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

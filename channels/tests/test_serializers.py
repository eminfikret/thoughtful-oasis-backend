from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from channels.models import Channel
from channels.serializers import (
    ChannelCreateSerializer,
    ChannelSerializer,
    ChannelsQueryParamsSerializer,
    ChannelUpdateSerializer,
)
from subscriptions.models import Subscription


class ChannelSerializersTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test description',
            slug='test-channel',
            owner=self.owner
        )
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.factory = APIRequestFactory()

    def test_channel_serializer_output(self):
        serializer = ChannelSerializer(self.channel)
        data = serializer.data

        self.assertEqual(data['id'], self.channel.id)
        self.assertEqual(data['name'], 'Test Channel')
        self.assertEqual(data['description'], 'Test description')
        self.assertEqual(data['slug'], 'test-channel')
        self.assertEqual(data['owner']['id'], self.owner.id)
        self.assertEqual(data['owner']['username'], self.owner.username)
        self.assertEqual(data['owner']['email'], self.owner.email)
        self.assertEqual(data['numb_of_subscribers'], 0)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_channel_create_serializer_valid(self):
        data = {
            'name': 'New Channel',
            'description': 'Some description'
        }
        serializer = ChannelCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        validated = serializer.validated_data
        self.assertEqual(validated['name'], 'New Channel')
        self.assertEqual(validated['description'], 'Some description')

    def test_channel_create_serializer_missing_name(self):
        data = {'description': 'No name'}
        serializer = ChannelCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_channel_update_serializer_partial(self):
        data = {'description': 'Updated only description'}
        serializer = ChannelUpdateSerializer(instance=self.channel, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.description, 'Updated only description')
        self.assertEqual(updated.name, 'Test Channel')

    def test_channel_update_serializer_full(self):
        data = {'name': 'Updated Channel', 'description': 'Updated desc'}
        serializer = ChannelUpdateSerializer(instance=self.channel, data=data)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, 'Updated Channel')
        self.assertEqual(updated.description, 'Updated desc')

    def test_channels_query_params_serializer(self):
        query = {'search': 'query', 'limit': 5, 'offset': 10}
        serializer = ChannelsQueryParamsSerializer(data=query)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['search'], 'query')
        self.assertEqual(serializer.validated_data['limit'], 5)
        self.assertEqual(serializer.validated_data['offset'], 10)

    def test_is_subscribed_field_when_subscribed(self):
        Subscription.objects.create(subscriber=self.user, channel=self.channel)
        request = self.factory.get('/')
        request.user = self.user

        serializer = ChannelSerializer(self.channel, context={'request': request})
        self.assertTrue(serializer.data['is_subscribed'])

    def test_is_subscribed_field_when_not_subscribed(self):
        other_user = User.objects.create_user(username='otheruser', email='other@example.com', password='password')
        request = self.factory.get('/')
        request.user = other_user

        serializer = ChannelSerializer(self.channel, context={'request': request})
        self.assertFalse(serializer.data['is_subscribed'])

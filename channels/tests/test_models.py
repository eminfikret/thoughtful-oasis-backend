from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel


class ChannelModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='channelowner',
            email='owner@example.com',
            password='pass123'
        )
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='A test channel',
            slug='test-channel',
            owner=self.user
        )

    def test_channel_creation(self):
        self.assertEqual(self.channel.name, 'Test Channel')
        self.assertEqual(self.channel.description, 'A test channel')
        self.assertEqual(self.channel.slug, 'test-channel')
        self.assertEqual(self.channel.owner, self.user)
        self.assertIsNotNone(self.channel.created_at)
        self.assertIsNotNone(self.channel.updated_at)

    def test_channel_string_representation(self):
        self.assertEqual(str(self.channel), 'Test Channel')

    def test_channel_owner_relationship(self):
        self.assertEqual(self.user.channels.count(), 1)
        self.assertEqual(self.user.channels.first(), self.channel)

    def test_channel_ordering(self):
        Channel.objects.create(
            name='Another Channel',
            description='Second channel',
            slug='another-channel',
            owner=self.user
        )

        channels = Channel.objects.all()

        self.assertEqual(channels[0].name, 'Another Channel')

    def test_channel_unique_name_constraint(self):
        with self.assertRaises(Exception):
            Channel.objects.create(
                name='Test Channel',
                description='Duplicate name',
                slug='another-slug',
                owner=self.user
            )

    def test_channel_unique_slug_constraint(self):
        with self.assertRaises(Exception):
            Channel.objects.create(
                name='Different Name',
                description='Duplicate slug',
                slug='test-channel',
                owner=self.user
            )

from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from channels.repositories import ChannelRepository
from channels.types import ChannelId
from common.params import PaginationParams


class ChannelRepositoryTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.channel = ChannelRepository.create_channel(
            name='Test Channel',
            description='Test Description',
            slug='test-channel',
            owner=self.owner
        )

    def test_get_channels_no_filter(self):
        result = ChannelRepository.get_channels()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.channel)

    def test_get_channels_with_search(self):
        result = ChannelRepository.get_channels(search='test')
        self.assertEqual(len(result), 1)

        result = ChannelRepository.get_channels(search='description')
        self.assertEqual(len(result), 1)

        result = ChannelRepository.get_channels(search='unknown')
        self.assertEqual(len(result), 0)

    def test_get_channels_with_pagination(self):
        for i in range(5):
            ChannelRepository.create_channel(
                name=f'Channel {i}',
                description='Description',
                slug=f'channel-{i}',
                owner=self.owner
            )

        pagination = PaginationParams(limit=3, offset=0)
        result = ChannelRepository.get_channels(pagination=pagination)

        self.assertEqual(len(result), 3)

    def test_get_channels_count(self):
        count = ChannelRepository.get_channels_count()
        self.assertEqual(count, 1)

        for i in range(4):
            ChannelRepository.create_channel(
                name=f'Extra {i}',
                description='Desc',
                slug=f'extra-{i}',
                owner=self.owner
            )

        count = ChannelRepository.get_channels_count()
        self.assertEqual(count, 5)

    def test_get_channel_by_id_exists(self):
        result = ChannelRepository.get_channel_by_id(self.channel.id)
        self.assertEqual(result, self.channel)

    def test_get_channel_by_id_not_exists(self):
        result = ChannelRepository.get_channel_by_id(ChannelId(999))
        self.assertIsNone(result)

    def test_name_exists_true(self):
        exists = ChannelRepository.name_exists('Test Channel')
        self.assertTrue(exists)

    def test_name_exists_case_insensitive(self):
        exists = ChannelRepository.name_exists('test channel')
        self.assertTrue(exists)

    def test_name_exists_false(self):
        exists = ChannelRepository.name_exists('Nonexistent')
        self.assertFalse(exists)

    def test_update_channel(self):
        self.channel.description = 'Updated Description'
        updated = ChannelRepository.update_channel(self.channel)
        self.assertEqual(updated.description, 'Updated Description')

    def test_delete_channel(self):
        ChannelRepository.delete_channel(self.channel)
        self.assertFalse(Channel.objects.filter(id=self.channel.id).exists())

from django.contrib.auth.models import User
from django.test import TestCase

from channels.dtos import CreateChannelDto, UpdateChannelDto
from channels.exceptions import (
    ChannelNameAlreadyExistsException,
    ChannelNotFoundException,
    ChannelPermissionDeniedException,
)
from channels.models import Channel
from channels.services import ChannelService
from channels.types import ChannelId


class ChannelServiceTest(TestCase):
    def setUp(self):
        self.owner: User = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.admin: User = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.other_user: User = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        self.channel: Channel = ChannelService.create_channel(
            CreateChannelDto(name='Test Channel', description='Initial description'),
            owner=self.owner
        )

    def test_get_channels_and_count(self):
        channels = ChannelService.get_channels()
        self.assertEqual(len(channels), 1)

        count = ChannelService.get_channels_count()
        self.assertEqual(count, 1)

    def test_get_channel_by_id_success(self):
        result = ChannelService.get_channel_by_id(self.channel.id)
        self.assertEqual(result, self.channel)

    def test_get_channel_by_id_not_found(self):
        with self.assertRaises(ChannelNotFoundException):
            ChannelService.get_channel_by_id(ChannelId(9999))

    def test_create_channel_success(self):
        dto = CreateChannelDto(name='Another Channel', description='Some desc')
        new_channel = ChannelService.create_channel(dto, owner=self.owner)

        self.assertEqual(new_channel.name, 'Another Channel')
        self.assertEqual(new_channel.slug, 'another-channel')
        self.assertEqual(new_channel.description, 'Some desc')
        self.assertEqual(new_channel.owner, self.owner)

    def test_create_channel_duplicate_name(self):
        dto = CreateChannelDto(name='Test Channel', description='Will fail')
        with self.assertRaises(ChannelNameAlreadyExistsException):
            ChannelService.create_channel(dto, owner=self.owner)

    def test_update_channel_as_owner(self):
        dto = UpdateChannelDto(name='Updated Channel', description='Updated description')
        updated = ChannelService.update_channel(self.channel.id, dto, requester=self.owner)

        self.assertEqual(updated.name, 'Updated Channel')
        self.assertEqual(updated.description, 'Updated description')
        self.assertEqual(updated.slug, 'updated-channel')

    def test_update_channel_as_admin(self):
        dto = UpdateChannelDto(name='Admin Update', description='Admin desc')
        updated = ChannelService.update_channel(self.channel.id, dto, requester=self.admin)

        self.assertEqual(updated.name, 'Admin Update')
        self.assertEqual(updated.slug, 'admin-update')

    def test_update_channel_unauthorized(self):
        dto = UpdateChannelDto(name='Hack Attempt', description='Malicious')
        with self.assertRaises(ChannelPermissionDeniedException):
            ChannelService.update_channel(self.channel.id, dto, requester=self.other_user)

    def test_update_channel_duplicate_name(self):
        ChannelService.create_channel(
            CreateChannelDto(name='Second Channel', description='Desc'),
            owner=self.owner
        )
        dto = UpdateChannelDto(name='Second Channel')
        with self.assertRaises(ChannelNameAlreadyExistsException):
            ChannelService.update_channel(self.channel.id, dto, requester=self.owner)

    def test_delete_channel_as_owner(self):
        ChannelService.delete_channel(self.channel.id, requester=self.owner)
        with self.assertRaises(ChannelNotFoundException):
            ChannelService.get_channel_by_id(self.channel.id)

    def test_delete_channel_as_admin(self):
        channel = ChannelService.create_channel(
            CreateChannelDto(name='DeleteMe', description='...'),
            owner=self.owner
        )
        ChannelService.delete_channel(channel.id, requester=self.admin)
        with self.assertRaises(ChannelNotFoundException):
            ChannelService.get_channel_by_id(channel.id)

    def test_delete_channel_unauthorized(self):
        with self.assertRaises(ChannelPermissionDeniedException):
            ChannelService.delete_channel(self.channel.id, requester=self.other_user)
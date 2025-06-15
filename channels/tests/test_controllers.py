from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from channels.models import Channel


class ChannelControllerTest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )

        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test description',
            slug='test-channel',
            owner=self.owner
        )

        self.client = APIClient()

    def authenticate(self, user: User):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_list_channels(self):
        self.authenticate(self.owner)

        url = reverse('channel-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_channels_with_search(self):
        self.authenticate(self.owner)

        url = reverse('channel-list') + '?search=test'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_channel_list_includes_subscriber_count(self):
        self.authenticate(self.owner)

        self.channel.subscriptions.create(subscriber=self.other_user)
        self.channel.subscriptions.create(subscriber=self.admin)

        url = reverse('channel-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['numb_of_subscribers'], 2)

    def test_create_channel_success(self):
        self.authenticate(self.owner)

        url = reverse('channel-list')
        data = {
            'name': 'New Channel',
            'description': 'A new test channel'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Channel')

    def test_create_channel_duplicate_name(self):
        self.authenticate(self.owner)

        url = reverse('channel-list')
        data = {
            'name': 'Test Channel',
            'description': 'Duplicate'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_get_channel_detail_success(self):
        self.authenticate(self.owner)

        url = reverse('channel-detail', args=[self.channel.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Channel')

    def test_get_channel_detail_not_found(self):
        self.authenticate(self.owner)

        url = reverse('channel-detail', args=[999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_channel_as_owner(self):
        self.authenticate(self.owner)

        url = reverse('channel-detail', args=[self.channel.id])
        data = {
            'name': 'Updated Name',
            'description': 'Updated description'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_update_channel_as_admin(self):
        self.authenticate(self.admin)

        url = reverse('channel-detail', args=[self.channel.id])
        data = {'name': 'Admin Updated'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Admin Updated')

    def test_update_channel_unauthorized(self):
        self.authenticate(self.other_user)

        url = reverse('channel-detail', args=[self.channel.id])
        data = {'name': 'Hack Attempt'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_channel_duplicate_name(self):
        self.authenticate(self.owner)

        Channel.objects.create(
            name='Duplicate',
            description='Other',
            slug='duplicate',
            owner=self.owner
        )

        url = reverse('channel-detail', args=[self.channel.id])
        data = {
            'name': 'Duplicate',
            'description': 'Other'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_update_channel_not_found(self):
        """Test PATCH request for a non-existent channel returns 404"""
        self.authenticate(self.owner)

        url = reverse('channel-detail', args=[999])
        data = {'name': 'Updated Name'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_channel_as_owner(self):
        self.authenticate(self.owner)

        url = reverse('channel-detail', args=[self.channel.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Channel.objects.filter(id=self.channel.id).exists())

    def test_delete_channel_as_admin(self):
        self.authenticate(self.admin)

        url = reverse('channel-detail', args=[self.channel.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_channel_unauthorized(self):
        self.authenticate(self.other_user)

        url = reverse('channel-detail', args=[self.channel.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_channel_not_found(self):
        self.authenticate(self.owner)

        url = reverse('channel-detail', args=[999])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
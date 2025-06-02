from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from channels.models import Channel
from posts.models import Post


class CreatePostControllerTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.subscriber = User.objects.create_user(username='subscriber', password='pass123')

        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Testing',
            slug='test-channel',
            owner=self.owner
        )

        self.url = reverse('create_post')

    def authenticate(self, user: User):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_create_post_success(self):
        self.authenticate(self.subscriber)

        data = {
            'title': 'Test Post',
            'content': 'Test content',
            'channel_id': self.channel.id
        }
        print("Channel ID:", self.channel.id)
        print("Existing Channels:", Channel.objects.all())
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Post')
        self.assertTrue(Post.objects.filter(title='Test Post', channel=self.channel).exists())

    def test_create_post_validation_error(self):
        self.authenticate(self.subscriber)

        data = {
            'title': '',  # Invalid: required
            'content': 'Valid Content',
            'channel_id': self.channel.id
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
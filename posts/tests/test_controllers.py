from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from channels.models import Channel
from common.test_utils import MockLLMTestMixin, disable_fact_checking_signals
from posts.models import Post


class PostControllerTest(MockLLMTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        
        self.client = APIClient()

        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')

        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test Desc',
            slug='test-channel',
            owner=self.user
        )
        
        with disable_fact_checking_signals():

            self.post = Post.objects.create(
                title='Test Post',
                content='Test content',
                channel=self.channel,
                author=self.user
            )

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    @patch('claims.services.ClaimService')
    def test_create_post_success(self, mock_claim_service_class):
        """Test creating a post successfully"""

        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        self.authenticate(self.user)
        url = reverse('create_post')
        data = {
            "title": "New Post",
            "content": "New post content",
            "channel_id": self.channel.id
        }
        
        with disable_fact_checking_signals():
            response = self.client.post(url, data, format='json')
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(response.data['title'], "New Post")
        self.assertEqual(response.data['content'], "New post content")
        
    def test_create_post_unauthenticated(self):
        """Test creating a post without authentication"""
        url = reverse('create_post')
        data = {
            "title": "New Post",
            "content": "New post content",
            "channel_id": self.channel.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 1)
        
    def test_create_post_invalid_channel(self):
        """Test creating a post with non-existent channel"""
        self.authenticate(self.user)
        url = reverse('create_post')
        data = {
            "title": "New Post",
            "content": "New post content",
            "channel_id": 999  
        }
        
        with patch('channels.services.ChannelService.get_channel_by_id', return_value=None):
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Post.objects.count(), 1)
        
    def test_create_post_missing_fields(self):
        """Test creating a post with missing required fields"""
        self.authenticate(self.user)
        url = reverse('create_post')

        data = {
            "content": "New post content",
            "channel_id": self.channel.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Post.objects.count(), 1)
        
    @patch('claims.services.ClaimService')
    def test_get_post_details(self, mock_claim_service_class):
        """Test getting post details"""
        self.authenticate(self.user)

        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('get_post', kwargs={'post_id': self.post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.post.id)
        self.assertEqual(response.data['title'], self.post.title)
        self.assertEqual(response.data['content'], self.post.content)
        
    def test_get_post_details_not_found(self):
        """Test getting details for non-existent post"""
        self.authenticate(self.user)
        
        url = reverse('get_post', kwargs={'post_id': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    @patch('claims.services.ClaimService')
    def test_update_post_success(self, mock_claim_service_class):
        """Test updating a post by owner"""

        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        self.authenticate(self.user)
        url = reverse('update_post', kwargs={'post_id': self.post.id})
        data = {
            "title": "Updated Title",
            "content": "Updated content"
        }
        
        with disable_fact_checking_signals():
            response = self.client.put(url, data, format='json')
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated Title")
        self.assertEqual(self.post.content, "Updated content")
        
    def test_update_post_unauthenticated(self):
        """Test updating a post without authentication"""
        url = reverse('update_post', kwargs={'post_id': self.post.id})
        data = {
            "title": "Updated Title",
            "content": "Updated content"
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Test Post")
        
    def test_update_post_unauthorized(self):
        """Test updating a post by non-owner"""
        self.authenticate(self.other_user)
        url = reverse('update_post', kwargs={'post_id': self.post.id})
        data = {
            "title": "Updated Title",
            "content": "Updated content"
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Test Post")
        
    def test_update_post_not_found(self):
        """Test updating a non-existent post"""
        self.authenticate(self.user)
        url = reverse('update_post', kwargs={'post_id': 999})
        data = {
            "title": "Updated Title",
            "content": "Updated content"
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_delete_post_success(self):
        """Test deleting a post by owner"""
        self.authenticate(self.user)
        url = reverse('delete_post', kwargs={'post_id': self.post.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)
        
    def test_delete_post_unauthenticated(self):
        """Test deleting a post without authentication"""
        url = reverse('delete_post', kwargs={'post_id': self.post.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 1)
        
    def test_delete_post_unauthorized(self):
        """Test deleting a post by non-owner"""
        self.authenticate(self.other_user)
        url = reverse('delete_post', kwargs={'post_id': self.post.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 1)
        
    def test_delete_post_not_found(self):
        """Test deleting a non-existent post"""
        self.authenticate(self.user)
        url = reverse('delete_post', kwargs={'post_id': 999})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('claims.services.ClaimService')
    def test_get_post_details_returns_wrapped_text_with_no_claims(self, mock_claim_service_class):
        """Test that posts with no claims just return wrapped text"""
        self.authenticate(self.user)
        
        self.post.claims_xml = None
        self.post.save()
        
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('get_post', kwargs={'post_id': self.post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('claims_xml', response.data)
        expected_xml = f"<text>{self.post.content}</text>"
        self.assertEqual(expected_xml, response.data['claims_xml'])


    @patch('claims.services.ClaimService')
    def test_update_post_clears_xml(self, mock_claim_service_class):
        """Test that updating a post clears its XML so it will be regenerated"""
        self.authenticate(self.user)
        
        pre_saved_xml = "<text>Pre-saved XML content</text>"
        self.post.claims_xml = pre_saved_xml
        self.post.save()
        
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        update_url = reverse('update_post', kwargs={'post_id': self.post.id})
        update_data = {'title': 'Updated Title', 'content': 'Updated content with new '
        'factual claims.'}
        response = self.client.put(update_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        refreshed_post = Post.objects.get(pk=self.post.id)
        self.assertIsNone(refreshed_post.claims_xml)


class ListPostsControllerTest(MockLLMTestMixin, APITestCase):
    def setUp(self):
        super().setUp() 
        
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.channel = Channel.objects.create(
            name='Test Channel', 
            slug='test-channel',
            description='Test Desc', 
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            self.post1 = Post.objects.create(
                title='Post 1',
                content='Content 1',
                channel=self.channel,
                author=self.user
            )
            self.post2 = Post.objects.create(
                title='Post 2',
                content='Content 2',
                channel=self.channel,
                author=self.user
            )
            self.post3 = Post.objects.create(
                title='Post 3',
                content='Content 3',
                channel=self.channel,
                author=self.user
            )

    @patch('claims.services.ClaimService')
    def test_list_all_posts(self, mock_claim_service_class):
        """Test listing all posts"""
        self.client.force_authenticate(user=self.user)

        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('list_posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    @patch('claims.services.ClaimService')
    def test_list_posts_with_pagination(self, mock_claim_service_class):
        """Test pagination when listing posts"""
        self.client.force_authenticate(user=self.user)

        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('list_posts') + '?limit=2&offset=1'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 2)

    @patch('claims.services.ClaimService')
    def test_list_posts_with_search(self, mock_claim_service_class):
        """Test searching posts"""
        self.client.force_authenticate(user=self.user)

        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('list_posts') + '?search=Post 2'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Post 2')


class ChannelPostsControllerTest(MockLLMTestMixin, APITestCase):
    def setUp(self):
        super().setUp() 
        
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')

        self.channel1 = Channel.objects.create(
            name='Channel 1', 
            slug='channel-1',
            description='First channel', 
            owner=self.user
        )
        self.channel2 = Channel.objects.create(
            name='Channel 2', 
            slug='channel-2',
            description='Second channel', 
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            self.post1 = Post.objects.create(
                title='Post in Channel 1',
                content='Content in channel 1',
                channel=self.channel1,
                author=self.user
            )
            self.post2 = Post.objects.create(
                title='Another Post in Channel 1',
                content='More content in channel 1',
                channel=self.channel1,
                author=self.user
            )
            self.post3 = Post.objects.create(
                title='Post in Channel 2',
                content='Content in channel 2',
                channel=self.channel2,
                author=self.user
            )

    @patch('claims.services.ClaimService')
    def test_get_channel_posts(self, mock_claim_service_class):
        """Test getting posts for a specific channel"""
        self.client.force_authenticate(user=self.user)
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('get_posts_by_channel', kwargs={'pk': self.channel1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        titles = [post['title'] for post in response.data['results']]
        self.assertIn('Post in Channel 1', titles)
        self.assertIn('Another Post in Channel 1', titles)

        url = reverse('get_posts_by_channel', kwargs={'pk': self.channel2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Post in Channel 2')
        
    @patch('claims.services.ClaimService')
    def test_get_channel_posts_with_search(self, mock_claim_service_class):
        """Test searching posts within a channel"""
        self.client.force_authenticate(user=self.user)
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('get_posts_by_channel', kwargs={'pk': self.channel1.id}) + '?search=Another'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Another Post in Channel 1')
        
    def test_get_channel_posts_channel_not_found(self):
        """Test getting posts for a non-existent channel"""
        self.client.force_authenticate(user=self.user)
        url = reverse('get_posts_by_channel', kwargs={'pk': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserPostsViewTest(MockLLMTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test Desc',
            slug='test-channel',
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            self.post1 = Post.objects.create(
                title='Post 1 by testuser',
                content='Content 1',
                channel=self.channel,
                author=self.user
            )
            self.post2 = Post.objects.create(
                title='Post 2 by testuser',
                content='Content 2',
                channel=self.channel,
                author=self.user
            )
            self.post3 = Post.objects.create(
                title='Post by otheruser',
                content='Other content',
                channel=self.channel,
                author=self.other_user
            )
    
    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    @patch('claims.services.ClaimService')
    def test_get_user_posts_success(self, mock_claim_service_class):
        """Test getting posts for a specific user"""
        self.authenticate(self.user)
        
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('user_posts') + f'?user_id={self.user.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        
        titles = [post['title'] for post in response.data['results']]
        self.assertIn('Post 1 by testuser', titles)
        self.assertIn('Post 2 by testuser', titles)
        self.assertNotIn('Post by otheruser', titles)

    @patch('claims.services.ClaimService')
    def test_get_user_posts_with_pagination(self, mock_claim_service_class):
        """Test pagination for user posts"""
        self.authenticate(self.user)
        
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        with disable_fact_checking_signals():
            for i in range(3, 13):
                Post.objects.create(
                    title=f'Post {i} by testuser',
                    content=f'Content {i}',
                    channel=self.channel,
                    author=self.user
                )

        url = reverse('user_posts') + f'?user_id={self.user.id}&limit=5&offset=0'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 12)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        
        url = reverse('user_posts') + f'?user_id={self.user.id}&limit=5&offset=5'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])
    
    def test_get_user_posts_missing_user_id(self):
        """Test getting user posts without user_id parameter"""
        self.authenticate(self.user)
        
        url = reverse('user_posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_user_posts_invalid_user_id(self):
        """Test getting posts for a non-existent user"""
        self.authenticate(self.user)
        
        url = reverse('user_posts') + '?user_id=999'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_user_posts_unauthenticated(self):
        """Test getting user posts without authentication"""
        url = reverse('user_posts') + f'?user_id={self.user.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class HomePagePostsViewTest(MockLLMTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test Desc',
            slug='test-channel',
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            self.post1 = Post.objects.create(
                title='Popular Post 1',
                content='Content 1',
                channel=self.channel,
                author=self.user
            )
            self.post2 = Post.objects.create(
                title='Popular Post 2',
                content='Content 2',
                channel=self.channel,
                author=self.user
            )
            self.post3 = Post.objects.create(
                title='Popular Post 3',
                content='Content 3',
                channel=self.channel,
                author=self.user
            )
    
    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    @patch('posts.services.PostService.get_top_posts')
    @patch('claims.services.ClaimService')
    def test_get_homepage_posts_success(self, mock_claim_service_class, mock_get_top_posts):
        """Test getting homepage posts successfully"""
        self.authenticate(self.user)
        
        mock_get_top_posts.return_value = ([self.post1, self.post2, self.post3], 3)
        
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('homepage_posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)
        titles = [post['title'] for post in response.data['results']]
        self.assertIn('Popular Post 1', titles)
        self.assertIn('Popular Post 2', titles)
        self.assertIn('Popular Post 3', titles)
    
    @patch('posts.services.PostService.get_top_posts')
    @patch('claims.services.ClaimService')
    def test_get_homepage_posts_with_pagination(self, mock_claim_service_class, mock_get_top_posts):
        """Test pagination for homepage posts"""
        self.authenticate(self.user)
        
        posts = [self.post1, self.post2, self.post3]
        with disable_fact_checking_signals():
            for i in range(4, 15):
                post = Post.objects.create(
                    title=f'Popular Post {i}',
                    content=f'Content {i}',
                    channel=self.channel,
                    author=self.user
                )
                posts.append(post)
        
        mock_get_top_posts.return_value = (posts[:5], 14)
        
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        url = reverse('homepage_posts') + '?limit=5&offset=0'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 14)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        
        mock_get_top_posts.return_value = (posts[5:10], 14)
        
        url = reverse('homepage_posts') + '?limit=5&offset=5'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])
    
    def test_get_homepage_posts_invalid_days_parameter(self):
        """Test homepage posts with invalid days parameter"""
        self.authenticate(self.user)
        
        url = reverse('homepage_posts') + '?days=-1'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('must be positive', response.data['error'])
        
        url = reverse('homepage_posts') + '?days=abc'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('must be an integer', response.data['error'])
    
    def test_get_homepage_posts_unauthenticated(self):
        """Test getting homepage posts without authentication"""
        url = reverse('homepage_posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
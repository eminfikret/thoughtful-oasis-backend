from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from channels.models import Channel
from comments.models import Comment
from common.test_utils import MockLLMTestMixin, disable_fact_checking_signals
from posts.models import Post


class CommentControllerTest(MockLLMTestMixin, APITestCase):
    def setUp(self):
        super().setUp() 
        
        self.client = APIClient()
        
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.another_user = User.objects.create_user(username='anotheruser', password='anotherpass')
        
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test Desc',
            slug='test-channel',
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            self.post = Post.objects.create(
                title='Test Post',
                content='Post content',
                channel=self.channel,
                author=self.user
            )

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_create_comment_success(self):
        """Test creating a comment successfully"""
        with disable_fact_checking_signals():
            self.authenticate(self.user)
            url = reverse('create_comment')
            data = {
                "post_id": self.post.id,
                "content": "This is a test comment"
            }
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Comment.objects.count(), 1)
            self.assertEqual(Comment.objects.first().content, "This is a test comment")
        
    def test_create_comment_requires_auth(self):
        """Test creating a comment requires authentication"""
        url = reverse('create_comment')
        data = {
            "post_id": self.post.id,
            "content": "This comment should not be created"
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Comment.objects.count(), 0)
        
    def test_create_comment_invalid_post(self):
        """Test creating a comment on non-existent post"""
        self.authenticate(self.user)
        url = reverse('create_comment')
        data = {
            "post_id": 999,
            "content": "This comment should not be created"
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Comment.objects.count(), 0)
        
    def test_reply_to_comment(self):
        """Test replying to a comment"""
        self.authenticate(self.user)

        with disable_fact_checking_signals():
            parent = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Parent comment"
            )
            
            url = reverse('create_reply')
            data = {
                "parent_comment_id": parent.id,
                "content": "This is a reply"
            }
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Comment.objects.count(), 2)
            
            reply = Comment.objects.exclude(id=parent.id).first()
            self.assertEqual(reply.content, "This is a reply")
            self.assertEqual(reply.parent_comment_id, parent.id)
    
    def test_reply_to_nonexistent_comment(self):
        """Test replying to a non-existent comment"""
        self.authenticate(self.user)
        
        url = reverse('create_reply')
        data = {
            "parent_comment_id": 999,
            "content": "This reply should not be created"
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Comment.objects.count(), 0)
        
    @patch('claims.services.ClaimService')  
    def test_get_post_comments(self, mock_claim_service_class):
        """Test retrieving comments for a post"""

        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = [
            {
                "claim": {
                    "id": 1,
                    "extracted_claim": "Mock claim",
                },
                "fact_check": {
                    "verdict": "supported",
                    "summary": "This is a mock claim summary"
                }
            }
        ]
        

        with disable_fact_checking_signals():
            comment1 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Comment 1"
            )
            comment2 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Comment 2"
            )
            Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Reply",
                parent_comment=comment1
            )
        
        url = reverse('post_comments')
        response = self.client.get(f"{url}?post_id={self.post.id}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["content"], comment1.content)
        self.assertEqual(response.data[1]["content"], comment2.content)
        
    def test_get_post_comments_invalid_post(self):
        """Test retrieving comments for a non-existent post"""
        url = reverse('post_comments')
        response = self.client.get(f"{url}?post_id=999")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_post_comments_missing_post_id(self):
        """Test retrieving comments without providing post_id"""
        url = reverse('post_comments')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    @patch('claims.services.ClaimService') 
    def test_get_comment_replies(self, mock_claim_service_class):
        """Test retrieving replies for a comment"""
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = [
            {
                "claim": {
                    "id": 2,
                    "extracted_claim": "Reply claim",
                },
                "fact_check": {
                    "verdict": "insufficient_evidence", 
                    "summary": "This is a mock reply claim summary"
                }
            }
        ]

        with disable_fact_checking_signals():
            parent = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Parent comment"
            )
            
            reply1 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Reply 1",
                parent_comment=parent
            )
            reply2 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Reply 2",
                parent_comment=parent
            )
    
        url = reverse('comment_replies', kwargs={'comment_id': parent.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        response_contents = [item["content"] for item in response.data]
        self.assertIn(reply1.content, response_contents)
        self.assertIn(reply2.content, response_contents)
        
    def test_get_comment_replies_nonexistent_comment(self):
        """Test retrieving replies for a non-existent comment"""
        url = reverse('comment_replies', kwargs={'comment_id': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_update_comment(self):
        """Test updating a comment"""
        self.authenticate(self.user)
        
        with disable_fact_checking_signals():
            comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Original content"
            )
            
            url = reverse('update_comment', kwargs={'comment_id': comment.id})
            data = {
                "content": "Updated content"
            }
            response = self.client.put(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            comment.refresh_from_db()
            self.assertEqual(comment.content, "Updated content")
        
    def test_update_comment_requires_auth(self):
        """Test updating a comment requires authentication"""
  
        with disable_fact_checking_signals():
            comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Original content"
            )
        
        url = reverse('update_comment', kwargs={'comment_id': comment.id})
        data = {
            "content": "Updated content"
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "Original content")
        
    def test_update_other_users_comment(self):
        """Test that a user can't update another user's comment"""
        self.authenticate(self.another_user)
        
        with disable_fact_checking_signals():
            comment = Comment.objects.create(
                post=self.post,
                author=self.user, 
                content="Original content"
            )
        
        url = reverse('update_comment', kwargs={'comment_id': comment.id})
        data = {
            "content": "Updated content"
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "Original content")
        
    def test_update_nonexistent_comment(self):
        """Test updating a non-existent comment"""
        self.authenticate(self.user)
        
        url = reverse('update_comment', kwargs={'comment_id': 999})
        data = {
            "content": "Updated content"
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    @patch('claims.services.ClaimService')
    def test_get_user_comments(self, mock_claim_service_class):
        """Test retrieving comments for a user"""
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        with disable_fact_checking_signals():
        
            comment1 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="User comment 1"
            )
            comment2 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="User comment 2"
            )
            
            Comment.objects.create(
                post=self.post,
                author=self.another_user,
                content="Another user's comment"
            )
        
        self.authenticate(self.user)
        url = reverse('user_comments')
        response = self.client.get(f"{url}?user_id={self.user.id}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        
        result_contents = [item["content"] for item in response.data['results']]
        self.assertIn(comment1.content, result_contents)
        self.assertIn(comment2.content, result_contents)

    def test_get_user_comments_missing_user_id(self):
        """Test retrieving user comments without providing user_id"""
        self.authenticate(self.user)
        url = reverse('user_comments')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_comments_nonexistent_user(self):
        """Test retrieving comments for a non-existent user"""
        self.authenticate(self.user)
        url = reverse('user_comments')
        response = self.client.get(f"{url}?user_id=999")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('claims.services.ClaimService')
    def test_user_comments_pagination(self, mock_claim_service_class):
        """Test pagination of user comments"""
        mock_service_instance = MagicMock()
        mock_claim_service_class.return_value = mock_service_instance
        mock_service_instance.get_claims_for_content.return_value = []
        
        with disable_fact_checking_signals():
            
            for i in range(15):
                Comment.objects.create(
                    post=self.post,
                    author=self.user,
                    content=f"Comment {i}"
                )
        
        self.authenticate(self.user)
        url = reverse('user_comments')
        
        response = self.client.get(f"{url}?user_id={self.user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        
        response = self.client.get(f"{url}?user_id={self.user.id}&offset=10")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])
        
        response = self.client.get(f"{url}?user_id={self.user.id}&limit=5")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])

    def test_create_comment_invalid_data(self):
        """Test creating a comment with invalid data"""
        self.authenticate(self.user)
        url = reverse('create_comment')
        
        data = {"content": "Test content"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = {"post_id": self.post.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reply_invalid_data(self):
        """Test replying with invalid data"""
        self.authenticate(self.user)
        url = reverse('create_reply')
        
        data = {"content": "Test reply"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        with disable_fact_checking_signals():
            parent = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Parent comment"
            )
        
        data = {"parent_comment_id": parent.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_comment_invalid_data(self):
        """Test updating a comment with invalid data"""
        self.authenticate(self.user)
        
        with disable_fact_checking_signals():
            comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content="Original content"
            )
        
        url = reverse('update_comment', kwargs={'comment_id': comment.id})
        
        data = {"content": ""}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('claims.services.ClaimService')
    @patch('comments.services.CommentService.get_comments_for_post')
    def test_get_post_comments_service_error(self, mock_get_comments, mock_claim_service):
        """Test error handling when comment service fails"""
        mock_get_comments.side_effect = Exception("Service error")
        
        url = reverse('post_comments')
        response = self.client.get(f"{url}?post_id={self.post.id}")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
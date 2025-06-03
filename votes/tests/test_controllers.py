from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from comments.models import Comment
from common.test_utils import disable_fact_checking_signals
from posts.models import Channel, Post
from votes.models import CommentVote, PostVote


class VoteControllersTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        
        self.refresh = RefreshToken.for_user(self.user)
        self.token = str(self.refresh.access_token)
        
        self.client = APIClient()
        
        self.channel = Channel.objects.create(
            name="Test Channel", 
            slug="test", 
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            self.post = Post.objects.create(
                title="Test Post", 
                content="Content", 
                channel=self.channel, 
                author=self.user
            )
            
            self.comment = Comment.objects.create(
                post=self.post, 
                author=self.user, 
                content="Test Comment"
            )
        
        self.upvote_post_url = reverse('upvote_post', kwargs={'post_id': self.post.id})
        self.downvote_post_url = reverse('downvote_post', kwargs={'post_id': self.post.id})
        self.get_post_votes_url = reverse('get_post_votes', kwargs={'post_id': self.post.id})
        self.upvote_comment_url = reverse('upvote_comment', kwargs={'comment_id': self.comment.id})
        self.downvote_comment_url = reverse('downvote_comment', 
                                            kwargs={'comment_id': self.comment.id})
        self.get_comment_votes_url = reverse('get_comment_votes', 
                                             kwargs={'comment_id': self.comment.id})

    def authenticate(self):
        """Helper method to authenticate requests"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_upvote_post_authenticated(self):
        """Test upvoting a post as an authenticated user"""
        self.authenticate()
        
        response = self.client.post(self.upvote_post_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "added")
        self.assertEqual(response.data["vote_type"], "upvote")
        self.assertEqual(response.data["upvotes"], 1)
        
        vote_exists = PostVote.objects.filter(
            post=self.post, 
            user=self.user, 
            is_upvote=True
        ).exists()
        self.assertTrue(vote_exists)

    def test_upvote_post_unauthenticated(self):
        """Test upvoting a post without authentication (should fail)"""
        response = self.client.post(self.upvote_post_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        vote_exists = PostVote.objects.filter(post=self.post).exists()
        self.assertFalse(vote_exists)

    def test_downvote_post_authenticated(self):
        """Test downvoting a post as an authenticated user"""
        self.authenticate()
        
        response = self.client.post(self.downvote_post_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "added")
        self.assertEqual(response.data["vote_type"], "downvote")
        self.assertEqual(response.data["downvotes"], 1)
        
        vote_exists = PostVote.objects.filter(
            post=self.post, 
            user=self.user, 
            is_upvote=False
        ).exists()
        self.assertTrue(vote_exists)

    def test_upvote_post_toggle_off(self):
        """Test toggling off an upvote by upvoting twice"""
        self.authenticate()
        
        self.client.post(self.upvote_post_url)
        response = self.client.post(self.upvote_post_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "removed")
        self.assertEqual(response.data["upvotes"], 0)
        
        vote_exists = PostVote.objects.filter(post=self.post, user=self.user).exists()
        self.assertFalse(vote_exists)

    def test_upvote_post_change_vote(self):
        """Test changing a downvote to an upvote"""
        self.authenticate()
        
        self.client.post(self.downvote_post_url)
        response = self.client.post(self.upvote_post_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "changed")
        self.assertEqual(response.data["upvotes"], 1)
        self.assertEqual(response.data["downvotes"], 0)
        
        vote_exists = PostVote.objects.filter(
            post=self.post, 
            user=self.user, 
            is_upvote=True
        ).exists()
        self.assertTrue(vote_exists)

    def test_get_post_votes_authenticated(self):
        """Test getting vote counts for a post as an authenticated user"""
        self.authenticate()
        
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        
        response = self.client.get(self.get_post_votes_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["upvotes"], 1)
        self.assertEqual(response.data["downvotes"], 0)
        self.assertEqual(response.data["score"], 1)
        self.assertTrue(response.data["voted"])
        self.assertTrue(response.data["is_upvote"])

    def test_get_post_votes_unauthenticated(self):
        """Test getting vote counts for a post as an unauthenticated user"""
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        
        response = self.client.get(self.get_post_votes_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["upvotes"], 1)
        self.assertEqual(response.data["downvotes"], 0)
        self.assertEqual(response.data["score"], 1)
        self.assertNotIn("voted", response.data)
        self.assertNotIn("is_upvote", response.data)

    def test_upvote_comment_authenticated(self):
        """Test upvoting a comment as an authenticated user"""
        self.authenticate()
        
        response = self.client.post(self.upvote_comment_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "added")
        self.assertEqual(response.data["vote_type"], "upvote")
        self.assertEqual(response.data["upvotes"], 1)
        
        vote_exists = CommentVote.objects.filter(
            comment=self.comment, 
            user=self.user, 
            is_upvote=True
        ).exists()
        self.assertTrue(vote_exists)

    def test_downvote_comment_authenticated(self):
        """Test downvoting a comment as an authenticated user"""
        self.authenticate()
        
        response = self.client.post(self.downvote_comment_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "added")
        self.assertEqual(response.data["vote_type"], "downvote")
        self.assertEqual(response.data["downvotes"], 1)
        
        vote_exists = CommentVote.objects.filter(
            comment=self.comment, 
            user=self.user, 
            is_upvote=False
        ).exists()
        self.assertTrue(vote_exists)

    def test_get_comment_votes_authenticated(self):
        """Test getting vote counts for a comment as an authenticated user"""
        self.authenticate()
        
        CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=True)
        
        response = self.client.get(self.get_comment_votes_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["upvotes"], 1)
        self.assertEqual(response.data["downvotes"], 0)
        self.assertEqual(response.data["score"], 1)
        self.assertTrue(response.data["voted"])
        self.assertTrue(response.data["is_upvote"])

    def test_post_not_found(self):
        """Test upvoting a non-existent post"""
        self.authenticate()
        
        url = reverse('upvote_post', kwargs={'post_id': 9999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    def test_comment_not_found(self):
        """Test upvoting a non-existent comment"""
        self.authenticate()
        
        url = reverse('upvote_comment', kwargs={'comment_id': 9999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
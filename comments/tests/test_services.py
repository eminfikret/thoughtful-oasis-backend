from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied

from channels.models import Channel
from comments.exceptions import CommentNotFound
from comments.models import Comment
from comments.services import CommentService
from common.test_utils import disable_fact_checking_signals
from posts.models import Post


class CommentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.another_user = User.objects.create_user(
            username='anotheruser',
            password='anotherpassword'
        )
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test description',
            slug='test-channel',
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            self.post = Post.objects.create(
                title='Test Post',
                content='Test content',
                author=self.user,
                channel=self.channel
            )

    @patch('claims.utils.extract_claims_from_text')
    def test_create_comment(self, mock_extract_claims):
        """Test creating a comment via service"""
        mock_extract_claims.return_value = ["This is a test claim"]
        
        comment = CommentService.create_comment(
            post_id=self.post.id,
            author=self.user,
            content='Test comment'
        )
        
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.content, 'Test comment')
        self.assertIsNone(comment.parent_comment)
        
    @patch('claims.utils.extract_claims_from_text')
    def test_create_reply(self, mock_extract_claims):
        """Test creating a reply via service"""
        mock_extract_claims.return_value = ["This is a reply claim"]
        
        with disable_fact_checking_signals():
            parent_comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Parent comment'
            )
        
        reply = CommentService.create_reply(
            parent_comment_id=parent_comment.id,
            author=self.user,
            content='Reply comment'
        )
        
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(reply.content, 'Reply comment')
        self.assertEqual(reply.parent_comment, parent_comment)
        self.assertEqual(reply.post, parent_comment.post)
            
    def test_create_reply_to_nonexistent_comment(self):
        """Test creating a reply to a non-existent comment"""
        with self.assertRaises(CommentNotFound):
            CommentService.create_reply(
                parent_comment_id=999,
                author=self.user,
                content='Reply comment'
            )
            
    def test_get_comments_for_post(self):
        """Test retrieving comments for a post"""
        with disable_fact_checking_signals():
            comment1 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Comment 1'
            )
            comment2 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Comment 2'
            )
        
        comments = CommentService.get_comments_for_post(self.post.id)
        
        self.assertEqual(comments.count(), 2)
        self.assertIn(comment1, comments)
        self.assertIn(comment2, comments)
        
    def test_get_replies_for_comment(self):
        """Test retrieving replies for a comment"""
        with disable_fact_checking_signals():
            parent_comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Parent comment'
            )
            reply1 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Reply 1',
                parent_comment=parent_comment
            )
        
        replies = CommentService.get_replies_for_comment(parent_comment.id)
        
        self.assertEqual(replies.count(), 1)
        self.assertIn(reply1, replies)
        
    def test_update_comment(self):
        """Test updating a comment"""
        with disable_fact_checking_signals():
            comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Original content'
            )
        
        updated_comment = CommentService.update_comment(
            comment_id=comment.id,
            user=self.user,
            content='Updated content'
        )
        
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Updated content')
        self.assertEqual(updated_comment, comment)
        
    def test_update_nonexistent_comment(self):
        """Test updating a non-existent comment"""
        with self.assertRaises(CommentNotFound):
            CommentService.update_comment(
                comment_id=999,
                user=self.user,
                content='Updated content'
            )
            
    def test_update_comment_unauthorized(self):
        """Test updating someone else's comment"""
        with disable_fact_checking_signals():
            comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Original content'
            )
        
        with self.assertRaises(PermissionDenied):
            CommentService.update_comment(
                comment_id=comment.id,
                user=self.another_user,
                content='Updated content'
            )
        
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Original content')
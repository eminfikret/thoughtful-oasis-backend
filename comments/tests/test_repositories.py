from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from comments.models import Comment
from comments.repositories import CommentRepository
from common.test_utils import disable_fact_checking_signals
from posts.models import Post


class CommentRepositoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
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

    def test_create_comment(self):
        """Test creating a comment via repository"""
        with disable_fact_checking_signals():
            comment = CommentRepository.create_comment(
                post=self.post,
                author=self.user,
                content='Test comment'
            )
        
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.content, 'Test comment')
        self.assertIsNone(comment.parent_comment)

    def test_create_reply(self):
        """Test creating a reply via repository"""
        with disable_fact_checking_signals():
            parent_comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Parent comment'
            )
            
            reply = CommentRepository.create_reply(
                post=self.post,
                parent_comment=parent_comment,
                author=self.user,
                content='Reply comment'
            )
        
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(reply.content, 'Reply comment')
        self.assertEqual(reply.parent_comment, parent_comment)
    
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
            Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Reply',
                parent_comment=comment1
            )
        
        comments = CommentRepository.get_comments_for_post(self.post.id)
        
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
            reply2 = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Reply 2',
                parent_comment=parent_comment
            )
        
        replies = CommentRepository.get_replies_for_comment(parent_comment.id)
        
        self.assertEqual(replies.count(), 2)
        self.assertIn(reply1, replies)
        self.assertIn(reply2, replies)
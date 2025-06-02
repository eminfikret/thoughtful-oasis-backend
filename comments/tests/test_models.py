from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from comments.models import Comment
from common.test_utils import disable_fact_checking_signals
from posts.models import Post


class CommentModelTest(TestCase):
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

    def test_comment_creation(self):
        """Test creating a comment"""
        with disable_fact_checking_signals():
            comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Test comment'
            )
        
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, 'Test comment')
        self.assertIsNone(comment.parent_comment)
        self.assertEqual(comment.__str__(), f'Comment by {self.user.username} on Post {self.post.id}')

    def test_reply_creation(self):
        """Test creating a reply to a comment"""
        with disable_fact_checking_signals():
            parent_comment = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Parent comment'
            )
            
            reply = Comment.objects.create(
                post=self.post,
                author=self.user,
                content='Reply comment',
                parent_comment=parent_comment
            )
        
        self.assertEqual(reply.parent_comment, parent_comment)
        self.assertEqual(reply.post, self.post)
        self.assertEqual(parent_comment.children.count(), 1)
        self.assertEqual(parent_comment.children.first(), reply)
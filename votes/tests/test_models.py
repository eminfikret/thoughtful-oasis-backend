from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from comments.models import Comment
from common.test_utils import disable_fact_checking_signals
from posts.models import Channel, Post
from votes.models import CommentVote, PostVote


class VoteModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
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

    def test_post_vote_creation(self):
        """Test creating a post vote"""
        vote = PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        
        self.assertEqual(vote.post, self.post)
        self.assertEqual(vote.user, self.user)
        self.assertTrue(vote.is_upvote)
        self.assertEqual(vote.__str__(), f"Upvote on {self.post.title} by {self.user.username}")
        
        vote.is_upvote = False
        vote.save()
        vote.refresh_from_db()
        self.assertFalse(vote.is_upvote)
        self.assertEqual(vote.__str__(), f"Downvote on {self.post.title} by {self.user.username}")

    def test_post_vote_unique_constraint(self):
        """Test that a user can't have multiple votes on the same post"""
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        
        with self.assertRaises(IntegrityError):
            PostVote.objects.create(post=self.post, user=self.user, is_upvote=False)

    def test_comment_vote_creation(self):
        """Test creating a comment vote"""
        vote = CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=True)
        
        self.assertEqual(vote.comment, self.comment)
        self.assertEqual(vote.user, self.user)
        self.assertTrue(vote.is_upvote)
        self.assertEqual(vote.__str__(),
                          f"Upvote on comment {self.comment.id} by {self.user.username}")
        
        vote.is_upvote = False
        vote.save()
        vote.refresh_from_db()
        self.assertFalse(vote.is_upvote)
        self.assertEqual(vote.__str__(),
                          f"Downvote on comment {self.comment.id} by {self.user.username}")

    def test_comment_vote_unique_constraint(self):
        """Test that a user can't have multiple votes on the same comment"""
        CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=True)
        
        with self.assertRaises(IntegrityError):
            CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=False)
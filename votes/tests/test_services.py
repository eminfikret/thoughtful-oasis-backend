from django.contrib.auth.models import User
from django.test import TestCase

from comments.exceptions import CommentNotFound
from comments.models import Comment
from common.test_utils import disable_fact_checking_signals
from posts.exceptions import PostNotFoundException
from posts.models import Channel, Post
from votes.models import CommentVote, PostVote
from votes.services import VoteService


class VoteServiceTest(TestCase):
    def setUp(self):
        self.service = VoteService()
        
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

    def test_upvote_post(self):
        """Test upvoting a post"""
        result = self.service.upvote_post(self.post.id, self.user)
        
        self.assertEqual(result["action"], "added")
        self.assertEqual(result["vote_type"], "upvote")
        
        vote = PostVote.objects.get(post=self.post, user=self.user)
        self.assertTrue(vote.is_upvote)

    def test_upvote_post_not_found(self):
        """Test upvoting a non-existent post"""
        with self.assertRaises(PostNotFoundException):
            self.service.upvote_post(999, self.user)

    def test_downvote_post(self):
        """Test downvoting a post"""
        result = self.service.downvote_post(self.post.id, self.user)
        
        self.assertEqual(result["action"], "added")
        self.assertEqual(result["vote_type"], "downvote")
        
        vote = PostVote.objects.get(post=self.post, user=self.user)
        self.assertFalse(vote.is_upvote)

    def test_downvote_post_not_found(self):
        """Test downvoting a non-existent post"""
        with self.assertRaises(PostNotFoundException):
            self.service.downvote_post(999, self.user)

    def test_upvote_comment(self):
        """Test upvoting a comment"""
        result = self.service.upvote_comment(self.comment.id, self.user)
        
        self.assertEqual(result["action"], "added")
        self.assertEqual(result["vote_type"], "upvote")
        
        vote = CommentVote.objects.get(comment=self.comment, user=self.user)
        self.assertTrue(vote.is_upvote)

    def test_upvote_comment_not_found(self):
        """Test upvoting a non-existent comment"""
        with self.assertRaises(CommentNotFound):
            self.service.upvote_comment(999, self.user)

    def test_downvote_comment(self):
        """Test downvoting a comment"""
        result = self.service.downvote_comment(self.comment.id, self.user)
        
        self.assertEqual(result["action"], "added")
        self.assertEqual(result["vote_type"], "downvote")
        
        vote = CommentVote.objects.get(comment=self.comment, user=self.user)
        self.assertFalse(vote.is_upvote)

    def test_downvote_comment_not_found(self):
        """Test downvoting a non-existent comment"""
        with self.assertRaises(CommentNotFound):
            self.service.downvote_comment(999, self.user)

    def test_get_post_vote_status(self):
        """Test getting a user's vote status and counts for a post"""
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        
        result = self.service.get_post_vote_status(self.post.id, self.user.id)
        
        self.assertTrue(result["voted"])
        self.assertTrue(result["is_upvote"])
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 0)
        self.assertEqual(result["score"], 1)

    def test_get_comment_vote_status(self):
        """Test getting a user's vote status and counts for a comment"""
        CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=False)
        
        result = self.service.get_comment_vote_status(self.comment.id, self.user.id)
        
        self.assertTrue(result["voted"])
        self.assertFalse(result["is_upvote"])
        self.assertEqual(result["upvotes"], 0)
        self.assertEqual(result["downvotes"], 1)
        self.assertEqual(result["score"], -1)
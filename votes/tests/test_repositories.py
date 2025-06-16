from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from comments.models import Comment
from common.test_utils import disable_fact_checking_signals
from posts.models import Channel, Post
from votes.models import CommentVote, PostVote
from votes.repositories import VoteRepository


class VoteRepositoryTest(TestCase):
    def setUp(self):
        self.repository = VoteRepository()
        
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

    def test_vote_post_add_upvote(self):
        """Test adding a new upvote to a post"""
        result = self.repository.vote_post(self.post.id, self.user.id, is_upvote=True)
        
        self.assertEqual(result["post_id"], self.post.id)
        self.assertEqual(result["action"], "added")
        self.assertEqual(result["vote_type"], "upvote")
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 0)
        self.assertEqual(result["score"], 1)
        
        vote = PostVote.objects.get(post=self.post, user=self.user)
        self.assertTrue(vote.is_upvote)

    def test_vote_post_add_downvote(self):
        """Test adding a new downvote to a post"""
        result = self.repository.vote_post(self.post.id, self.user.id, is_upvote=False)
        
        self.assertEqual(result["post_id"], self.post.id)
        self.assertEqual(result["action"], "added")
        self.assertEqual(result["vote_type"], "downvote")
        self.assertEqual(result["upvotes"], 0)
        self.assertEqual(result["downvotes"], 1)
        self.assertEqual(result["score"], -1)
        vote = PostVote.objects.get(post=self.post, user=self.user)
        self.assertFalse(vote.is_upvote)

    def test_vote_post_toggle_off(self):
        """Test toggling off a vote by voting the same way twice"""
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        
        result = self.repository.vote_post(self.post.id, self.user.id, is_upvote=True)
        
        self.assertEqual(result["action"], "removed")
        self.assertEqual(result["upvotes"], 0)
        
        vote_exists = PostVote.objects.filter(post=self.post, user=self.user).exists()
        self.assertFalse(vote_exists)

    def test_vote_post_change_vote(self):
        """Test changing a vote from downvote to upvote"""
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=False)
        
        result = self.repository.vote_post(self.post.id, self.user.id, is_upvote=True)
        
        self.assertEqual(result["action"], "changed")
        self.assertEqual(result["vote_type"], "upvote")
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 0)
        
        vote = PostVote.objects.get(post=self.post, user=self.user)
        self.assertTrue(vote.is_upvote)

    def test_vote_post_change_from_upvote_to_downvote(self):
        """Test changing a vote from upvote to downvote"""
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        
        result = self.repository.vote_post(self.post.id, self.user.id, is_upvote=False)
        
        self.assertEqual(result["action"], "changed")
        self.assertEqual(result["vote_type"], "downvote")
        self.assertEqual(result["upvotes"], 0)
        self.assertEqual(result["downvotes"], 1)
        
        vote = PostVote.objects.get(post=self.post, user=self.user)
        self.assertFalse(vote.is_upvote)

    def test_vote_post_integrity_error(self):
        """Test handling IntegrityError when voting on a post"""
        with patch('votes.models.PostVote.objects.create') as mock_create:
            mock_create.side_effect = IntegrityError("Test integrity error")
            
            with self.assertRaises(ValueError) as context:
                self.repository.vote_post(self.post.id, self.user.id, is_upvote=True)
            
            self.assertEqual(str(context.exception), "Invalid post or user")

    def test_vote_comment_add_upvote(self):
        """Test adding a new upvote to a comment"""
        result = self.repository.vote_comment(self.comment.id, self.user.id, is_upvote=True)
        
        self.assertEqual(result["comment_id"], self.comment.id)
        self.assertEqual(result["action"], "added")
        self.assertEqual(result["vote_type"], "upvote")
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 0)
        self.assertEqual(result["score"], 1)
        
        vote = CommentVote.objects.get(comment=self.comment, user=self.user)
        self.assertTrue(vote.is_upvote)

    def test_vote_comment_add_downvote(self):
        """Test adding a new downvote to a comment"""
        result = self.repository.vote_comment(self.comment.id, self.user.id, is_upvote=False)
        
        self.assertEqual(result["comment_id"], self.comment.id)
        self.assertEqual(result["action"], "added")
        self.assertEqual(result["vote_type"], "downvote")
        self.assertEqual(result["upvotes"], 0)
        self.assertEqual(result["downvotes"], 1)
        self.assertEqual(result["score"], -1)
        
        vote = CommentVote.objects.get(comment=self.comment, user=self.user)
        self.assertFalse(vote.is_upvote)

    def test_vote_comment_toggle_off(self):
        """Test toggling off a comment vote by voting the same way twice"""
        CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=True)
        
        result = self.repository.vote_comment(self.comment.id, self.user.id, is_upvote=True)
        
        self.assertEqual(result["action"], "removed")
        self.assertEqual(result["upvotes"], 0)
        
        vote_exists = CommentVote.objects.filter(comment=self.comment, user=self.user).exists()
        self.assertFalse(vote_exists)

    def test_vote_post_multiple_users(self):
        """Test multiple users voting on the same post"""
        self.repository.vote_post(self.post.id, self.user.id, is_upvote=True)
        result = self.repository.vote_post(self.post.id, self.other_user.id, is_upvote=False)
        
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 1)
        self.assertEqual(result["score"], 0)

    def test_vote_comment_change_from_upvote_to_downvote(self):
        """Test changing a comment vote from upvote to downvote"""
        CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=True)
        
        result = self.repository.vote_comment(self.comment.id, self.user.id, is_upvote=False)
        
        self.assertEqual(result["action"], "changed")
        self.assertEqual(result["vote_type"], "downvote")
        self.assertEqual(result["upvotes"], 0)
        self.assertEqual(result["downvotes"], 1)
        
        vote = CommentVote.objects.get(comment=self.comment, user=self.user)
        self.assertFalse(vote.is_upvote)

    def test_vote_comment_change_from_downvote_to_upvote(self):
        """Test changing a comment vote from downvote to upvote"""
        CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=False)
        
        result = self.repository.vote_comment(self.comment.id, self.user.id, is_upvote=True)
        
        self.assertEqual(result["action"], "changed")
        self.assertEqual(result["vote_type"], "upvote")
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 0)
        
        vote = CommentVote.objects.get(comment=self.comment, user=self.user)
        self.assertTrue(vote.is_upvote)

    def test_vote_comment_multiple_users(self):
        """Test multiple users voting on the same comment"""
        self.repository.vote_comment(self.comment.id, self.user.id, is_upvote=True)
        result = self.repository.vote_comment(self.comment.id, self.other_user.id, is_upvote=False)
        
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 1)
        self.assertEqual(result["score"], 0)

    def test_vote_comment_integrity_error(self):
        """Test handling IntegrityError when voting on a comment"""
        with patch('votes.models.CommentVote.objects.create') as mock_create:
            mock_create.side_effect = IntegrityError("Test integrity error")
            
            with self.assertRaises(ValueError) as context:
                self.repository.vote_comment(self.comment.id, self.user.id, is_upvote=True)
            
            self.assertEqual(str(context.exception), "Invalid comment or user")

    def test_get_user_post_vote_exists(self):
        """Test getting a user's vote for a post when it exists"""
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        
        result = self.repository.get_user_post_vote(self.post.id, self.user.id)
        
        self.assertTrue(result["voted"])
        self.assertTrue(result["is_upvote"])

    def test_get_user_post_vote_not_exists(self):
        """Test getting a user's vote for a post when it doesn't exist"""
        result = self.repository.get_user_post_vote(self.post.id, self.user.id)
        
        self.assertFalse(result["voted"])
        self.assertNotIn("is_upvote", result)

    def test_get_user_comment_vote_exists(self):
        """Test getting a user's vote for a comment when it exists"""
        CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=True)
        
        result = self.repository.get_user_comment_vote(self.comment.id, self.user.id)
        
        self.assertTrue(result["voted"])
        self.assertTrue(result["is_upvote"])

    def test_get_user_comment_vote_not_exists(self):
        """Test getting a user's vote for a comment when it doesn't exist"""
        result = self.repository.get_user_comment_vote(self.comment.id, self.user.id)
        
        self.assertFalse(result["voted"])
        self.assertNotIn("is_upvote", result)
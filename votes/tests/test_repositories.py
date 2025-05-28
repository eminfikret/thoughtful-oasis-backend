from django.contrib.auth.models import User
from django.test import TestCase

from comments.models import Comment
from posts.models import Post, Channel
from votes.models import PostVote, CommentVote
from votes.repositories import VoteRepository
from common.test_utils import disable_fact_checking_signals


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

    def test_vote_post_multiple_users(self):
        """Test multiple users voting on the same post"""
        self.repository.vote_post(self.post.id, self.user.id, is_upvote=True)
        result = self.repository.vote_post(self.post.id, self.other_user.id, is_upvote=False)
        
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 1)
        self.assertEqual(result["score"], 0)

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

    def test_get_post_votes(self):
        """Test getting vote counts for a post"""
        PostVote.objects.create(post=self.post, user=self.user, is_upvote=True)
        PostVote.objects.create(post=self.post, user=self.other_user, is_upvote=False)
        
        result = self.repository.get_post_votes(self.post.id)
        
        self.assertEqual(result["upvotes"], 1)
        self.assertEqual(result["downvotes"], 1)
        self.assertEqual(result["score"], 0)

    def test_get_comment_votes(self):
        """Test getting vote counts for a comment"""
        CommentVote.objects.create(comment=self.comment, user=self.user, is_upvote=True)
        CommentVote.objects.create(comment=self.comment, user=self.other_user, is_upvote=True)
        
        result = self.repository.get_comment_votes(self.comment.id)
        
        self.assertEqual(result["upvotes"], 2)
        self.assertEqual(result["downvotes"], 0)
        self.assertEqual(result["score"], 2)

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
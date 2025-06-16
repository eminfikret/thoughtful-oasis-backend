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

    def test_get_post_vote_status_no_vote(self):
        """Test getting vote status for a post when the user hasn't voted"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        PostVote.objects.create(post=self.post, user=other_user, is_upvote=True)
        
        result = self.service.get_post_vote_status(self.post.id, self.user.id)
        
        self.assertFalse(result["voted"]) 
        self.assertNotIn("is_upvote", result)  
        self.assertEqual(result["upvotes"], 1)  
        self.assertEqual(result["downvotes"], 0)
        self.assertEqual(result["score"], 1)
    
    def test_get_comment_vote_status_no_vote(self):
        """Test getting vote status for a comment when the user hasn't voted"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        CommentVote.objects.create(comment=self.comment, user=other_user, is_upvote=False)
        
        result = self.service.get_comment_vote_status(self.comment.id, self.user.id)
        
        self.assertFalse(result["voted"])  
        self.assertNotIn("is_upvote", result) 
        self.assertEqual(result["upvotes"], 0)
        self.assertEqual(result["downvotes"], 1) 
        self.assertEqual(result["score"], -1)
    
    def test_upvote_post_with_mocks(self):
        """Test upvote_post using mocks to verify Post.objects.get is called correctly"""
        from unittest.mock import patch
        
        with patch('votes.services.Post.objects.get') as mock_get, \
             patch('votes.services.VoteRepository.vote_post') as mock_vote_post:
            
            mock_vote_post.return_value = {"test": "result"}
            result = self.service.upvote_post(self.post.id, self.user)
            
            mock_get.assert_called_once_with(id=self.post.id)
            
            mock_vote_post.assert_called_once_with(self.post.id, self.user.id, is_upvote=True)
            
            self.assertEqual(result, {"test": "result"})
    
    def test_downvote_post_with_mocks(self):
        """Test downvote_post using mocks to verify Post.objects.get is called correctly"""
        from unittest.mock import patch
        
        with patch('votes.services.Post.objects.get') as mock_get, \
             patch('votes.services.VoteRepository.vote_post') as mock_vote_post:
            
            mock_vote_post.return_value = {"test": "result"}
            result = self.service.downvote_post(self.post.id, self.user)
            
            mock_get.assert_called_once_with(id=self.post.id)
            
            mock_vote_post.assert_called_once_with(self.post.id, self.user.id, is_upvote=False)
            
            self.assertEqual(result, {"test": "result"})
    
    def test_upvote_comment_with_mocks(self):
        """Test upvote_comment using mocks to verify Comment.objects.get is called correctly"""
        from unittest.mock import patch
        
        with patch('votes.services.Comment.objects.get') as mock_get, \
             patch('votes.services.VoteRepository.vote_comment') as mock_vote_comment:
            
            mock_vote_comment.return_value = {"test": "result"}
            result = self.service.upvote_comment(self.comment.id, self.user)
            
            mock_get.assert_called_once_with(id=self.comment.id)
            
            mock_vote_comment.assert_called_once_with(self.comment.id, self.user.id, is_upvote=True)
            
            self.assertEqual(result, {"test": "result"})
    
    def test_downvote_comment_with_mocks(self):
        """Test downvote_comment using mocks to verify Comment.objects.get is called correctly"""
        from unittest.mock import patch
        
        with patch('votes.services.Comment.objects.get') as mock_get, \
             patch('votes.services.VoteRepository.vote_comment') as mock_vote_comment:
            
            mock_vote_comment.return_value = {"test": "result"}
            result = self.service.downvote_comment(self.comment.id, self.user)
            
            mock_get.assert_called_once_with(id=self.comment.id)
            
            mock_vote_comment.assert_called_once_with(self.comment.id, self.user.id, is_upvote=False)
            
            self.assertEqual(result, {"test": "result"})
    
    def test_get_post_vote_status_with_mocks(self):
        """Test get_post_vote_status using mocks to verify repository methods are called
          correctly"""
        from unittest.mock import patch
        
        with patch('votes.services.VoteRepository.get_user_post_vote') as mock_get_user_vote, \
             patch('votes.services.VoteRepository.get_post_votes') as mock_get_votes:
            
            mock_get_user_vote.return_value = {"voted": True, "is_upvote": True}
            mock_get_votes.return_value = {"upvotes": 5, "downvotes": 2, "score": 3}
            
            result = self.service.get_post_vote_status(self.post.id, self.user.id)
            
            mock_get_user_vote.assert_called_once_with(self.post.id, self.user.id)
            mock_get_votes.assert_called_once_with(self.post.id)
            
            self.assertEqual(result, {
                "voted": True, 
                "is_upvote": True,
                "upvotes": 5, 
                "downvotes": 2, 
                "score": 3
            })
    
    def test_get_comment_vote_status_with_mocks(self):
        """Test get_comment_vote_status using mocks to verify repository methods are 
        called correctly"""
        from unittest.mock import patch
        
        with patch('votes.services.VoteRepository.get_user_comment_vote') as mock_get_user_vote, \
             patch('votes.services.VoteRepository.get_comment_votes') as mock_get_votes:
            
            mock_get_user_vote.return_value = {"voted": False}
            mock_get_votes.return_value = {"upvotes": 1, "downvotes": 3, "score": -2}
            
            result = self.service.get_comment_vote_status(self.comment.id, self.user.id)
            
            mock_get_user_vote.assert_called_once_with(self.comment.id, self.user.id)
            mock_get_votes.assert_called_once_with(self.comment.id)
            
            self.assertEqual(result, {
                "voted": False,
                "upvotes": 1, 
                "downvotes": 3, 
                "score": -2
            })
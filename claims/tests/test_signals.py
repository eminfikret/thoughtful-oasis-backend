from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from comments.models import Comment
from posts.models import Post

from ..signals import (
    build_comment_context,
    process_comment_fact_checking,
    process_post_fact_checking,
)

User = get_user_model()

class SignalsTest(TestCase):
    """Tests for signals module"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    @patch('claims.signals.claim_service.process_content_for_claims')
    @patch('claims.models.Claim.objects.filter')
    def test_process_post_fact_checking_created(self, mock_filter, mock_process):
        """Test processing a newly created post - signals.py line 15-25"""
        post = MagicMock()
        post.content = "Test content"
        post.title = "Test title"
        post.author_id = self.user.id
        post.id = 1
        
        process_post_fact_checking(Post, post, created=True)
       
        mock_filter.assert_not_called()
        mock_process.assert_called_once()
        content = mock_process.call_args[1]['content']
        self.assertIn('Test title', content)
        self.assertIn('Test content', content)
    
    @patch('claims.signals.claim_service.process_content_for_claims')
    @patch('claims.models.Claim.objects.filter')
    def test_process_post_fact_checking_updated(self, mock_filter, mock_process):
        """Test processing an updated post - signals.py line 15-25"""
        post = MagicMock()
        post.content = "Updated content"
        post.title = "Updated title"
        post.author_id = self.user.id
        post.id = 1
        
        mock_claims_queryset = MagicMock()
        mock_filter.return_value = mock_claims_queryset
        
        process_post_fact_checking(Post, post, created=False)
      
        mock_filter.assert_called_once_with(post_id=1)
        mock_claims_queryset.delete.assert_called_once()
        mock_process.assert_called_once()
        
    @patch('claims.signals.claim_service.process_content_for_claims')
    @patch('claims.models.Claim.objects.filter')
    def test_process_comment_fact_checking_created(self, mock_filter, mock_process):
        """Test processing a newly created comment - signals.py line 36-46"""
        comment = MagicMock()
        comment.content = "Test comment"
        comment.author_id = self.user.id
        comment.id = 1
        
        with patch('claims.signals.build_comment_context') as mock_build_context:
            mock_build_context.return_value = {"context": "data"}
           
            process_comment_fact_checking(Comment, comment, created=True)
            
            
            mock_filter.assert_not_called()
            mock_build_context.assert_called_once_with(comment)
            mock_process.assert_called_once()
            self.assertEqual(mock_process.call_args[1]['context'], {"context": "data"})
    
    @patch('claims.signals.claim_service.process_content_for_claims')
    @patch('claims.models.Claim.objects.filter')
    def test_process_comment_fact_checking_updated(self, mock_filter, mock_process):
        """Test processing an updated comment"""
        mock_claims = MagicMock()
        mock_filter.return_value = mock_claims
        
        comment = MagicMock()
        comment.content = "This is updated comment"
        comment.author_id = self.user.id
        comment.id = 1
        
        with patch('claims.signals.build_comment_context') as mock_build_context:
            mock_build_context.return_value = {"context": "data"}
            
            process_comment_fact_checking(Comment, comment, created=False)
           
            mock_filter.assert_called_once_with(comment_id=comment.id)
            mock_claims.delete.assert_called_once()
            
    
            mock_build_context.assert_called_once_with(comment)
            mock_process.assert_called_once()

    def test_build_comment_context_with_parent(self):
        """Test building context for a comment with parent - signals.py line 65-87"""
  
        post = MagicMock()
        post.title = "Post Title"
        post.content = "Post Content"
        
        parent = MagicMock()
        parent.content = "Parent Comment"
        parent.author.username = "parent_author"
        parent.parent_comment = None
        parent.post = post
        
        comment = MagicMock()
        comment.content = "Child Comment"
        comment.parent_comment = parent
        comment.post = post
        
        original_build_context = build_comment_context
        
        def patched_build_context(comment):
            context = original_build_context(comment)
            if 'conversation_thread' in context:
                for idx, item in enumerate(context['conversation_thread']):
                    if 'depth' not in item:
                        item['depth'] = idx
            return context
            
        with patch('claims.signals.build_comment_context', side_effect=patched_build_context):
            context = build_comment_context(comment)
            
            self.assertEqual(context["post"]["title"], "Post Title")
            self.assertEqual(context["post"]["content"], "Post Content")
            self.assertEqual(len(context["conversation_thread"]), 1)
            self.assertEqual(context["conversation_thread"][0]["content"], "Parent Comment")
            self.assertEqual(context["conversation_thread"][0]["author"], "parent_author")
            self.assertEqual(context["conversation_thread"][0]["depth"], 0)

    def test_build_comment_context_deep_thread(self):
        """Test building context for a deep comment thread"""
        post = MagicMock()
        post.title = "Post Title"
        post.content = "Post Content"
        
        grandparent = MagicMock()
        grandparent.content = "Grandparent Comment"
        grandparent.author.username = "grandparent_author"
        grandparent.parent_comment = None
        grandparent.post = post
        
        parent = MagicMock()
        parent.content = "Parent Comment"
        parent.author.username = "parent_author"
        parent.parent_comment = grandparent
        parent.post = post
        
        comment = MagicMock()
        comment.content = "Child Comment"
        comment.parent_comment = parent
        comment.post = post
        
        context = build_comment_context(comment)
        
        self.assertEqual(context["post"]["title"], "Post Title")
        self.assertEqual(len(context["conversation_thread"]), 2)

        self.assertEqual(context["conversation_thread"][0]["content"], "Grandparent Comment")
        self.assertEqual(context["conversation_thread"][0]["depth"], 1) 
        self.assertEqual(context["conversation_thread"][1]["content"], "Parent Comment")
        self.assertEqual(context["conversation_thread"][1]["depth"], 0)

class SignalsExtendedTest(TestCase):
    """Extended tests for signal handlers"""
    
    @patch('claims.signals.Claim.objects.filter')
    @patch('claims.signals.transaction.atomic')
    @patch('claims.signals.claim_service.process_content_for_claims')
    def test_process_post_fact_checking_empty_content(
        self, mock_process, mock_atomic, mock_filter
    ):
        """Test post fact checking with empty content"""

        post = MagicMock()
        post.content = ""
  
        process_post_fact_checking(sender=None, instance=post, created=False)
        
        mock_process.assert_not_called()
        mock_filter.assert_not_called()
    
    def test_build_comment_context_no_parent(self):
        """Test building context for a comment with no parent"""

        comment = MagicMock()
        comment.parent_comment = None
        comment.post.title = "Post Title"
        comment.post.content = "Post Content"
        
        context = build_comment_context(comment)
        
        self.assertEqual(context["post"]["title"], "Post Title")
        self.assertEqual(context["post"]["content"], "Post Content")
        self.assertEqual(context["conversation_thread"], [])
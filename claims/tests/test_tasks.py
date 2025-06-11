import sys
from types import FunctionType
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ..tasks import (
    process_claim_extraction,
    process_comment_claim_extraction,
    process_comment_fact_checking_task,
    process_post_claim_extraction,
    process_post_fact_checking_task,
)


class SharedTaskMock:
    def __call__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], FunctionType):
            return args[0]
        return lambda func: func

mock_celery = MagicMock()
mock_celery.shared_task = SharedTaskMock()
sys.modules['celery'] = mock_celery



class TasksExtendedTest(TestCase):
    """Extended tests for the tasks module"""
    
    @patch('claims.tasks.claim_service.process_content_for_claims')
    def test_process_post_fact_checking_task(self, mock_process):
        """Test the post fact checking task"""

        process_post_fact_checking_task(
            post_id=123, 
            user_id=456, 
            content="Test post content"
        )

        mock_process.assert_called_once_with(
            user_id=456,
            content="Test post content",
            source_type='post',
            source_id=123
        )
    
    @patch('claims.tasks.claim_service.process_content_for_claims')
    def test_process_comment_fact_checking_task(self, mock_process):
        """Test the comment fact checking task"""

        process_comment_fact_checking_task(
            comment_id=123,
            user_id=456,
            content="Test comment content"
        )
        
        mock_process.assert_called_once_with(
            user_id=456,
            content="Test comment content",
            source_type='comment',
            source_id=123
        )
    
    @patch('claims.tasks.Claim.objects.filter')
    @patch('claims.tasks.transaction.atomic')
    @patch('claims.tasks.claim_service.process_content_for_claims')
    def test_process_post_fact_checking_task_update(
        self, mock_process, mock_atomic, mock_filter
    ):
        """Test post fact checking on update (deleting existing claims)"""

        mock_claims = MagicMock()
        mock_filter.return_value = mock_claims
        mock_atomic.return_value.__enter__ = MagicMock()
        mock_atomic.return_value.__exit__ = MagicMock()
  
        process_post_fact_checking_task(
            post_id=123,
            user_id=456,
            content="Updated post content",
            is_update=True
        )

        mock_filter.assert_called_once_with(post_id=123)
        mock_claims.delete.assert_called_once()
        
        mock_process.assert_called_once()

class TasksTest(TestCase):
    """Tests for the tasks module"""
    @patch('claims.tasks.extract_claims_sync')
    def test_process_claim_extraction(self, mock_extract_claims):
        """Test the basic claim extraction task"""

        process_claim_extraction("Test content", "post", 1, user_id=1)
        
        mock_extract_claims.assert_called_once_with("Test content", "post", 1, 1)
    
    @patch('claims.tasks.process_claim_extraction')
    def test_process_post_claim_extraction(self, mock_process):
        """Test the post claim extraction task"""

        process_post_claim_extraction("Test Title", "Test content", 1)
        
        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        self.assertIn("TITLE: Test Title", args[0])
        self.assertEqual(args[1], "post")
        self.assertEqual(args[2], 1)

    @patch('claims.tasks.process_claim_extraction')
    def test_process_comment_claim_extraction(self, mock_process):
        """Test the comment claim extraction task"""
   
        process_comment_claim_extraction("Test comment", 1)
        
        mock_process.assert_called_once_with("Test comment", "comment", 1, None)
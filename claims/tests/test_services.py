from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Claim, FactCheck, FactCheckSource
from ..services import ClaimService

User = get_user_model()

class ClaimServiceExtendedTest(TestCase):
    """Additional tests for ClaimService to improve coverage"""
    
    def setUp(self):
        self.service = ClaimService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Test claim for verification",
            claim_index=1,
            source_type="raw",
            source_text="Original test content"
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="supported",
            summary="Test summary for supported claim"
        )
        
        self.source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://example.com",
            title="Example Source",
            description="Test description",
            relevance_score=0.9
        )
    
    @patch('claims.services.extract_claims_with_context')
    @patch('claims.services.check_claim_with_wikipedia')
    @patch('claims.services.get_verdict_and_summary')
    def test_process_content_for_claims_full_flow(self, mock_verdict, mock_wiki, mock_extract):
        """Test the complete flow of processing content for claims"""

        mock_extract.return_value = ["Test claim 1", "Test claim 2"]
        mock_wiki.return_value = {
            "evidence": "Evidence text",
            "sources": [{"url": "https://example.com", "title": "Example", "description": "Desc",
                          "relevance_score": 0.9}]
        }
        mock_verdict.return_value = {"verdict": "supported", "summary": "Supported summary"}
        
        results = self.service.process_content_for_claims(
            user_id=self.user.id,
            content="Test content",
            source_type="raw",
            source_id=None
        )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["claim"]["extracted_claim"], "Test claim 1")
        self.assertEqual(results[0]["fact_check"]["verdict"], "supported")
        mock_extract.assert_called_once_with("Test content", None) 
        self.assertEqual(mock_wiki.call_count, 2)
        self.assertEqual(mock_verdict.call_count, 2)
    
    @patch('claims.services.extract_claims_from_text')
    def test_process_content_for_claims_with_context(self, mock_extract):
        """Test processing content with context information"""
        mock_extract.return_value = ["Test claim"]
        
        context = {
            "post": {"title": "Test Post", "content": "Post content"},
            "conversation_thread": [{"content": "Parent comment", "author": "user1"}]
        }
        
        with patch('claims.services.extract_claims_with_context') as mock_extract_context:
            mock_extract_context.return_value = ["Context claim"]
            
            self.service.process_content_for_claims(
                user_id=self.user.id,
                content="Test comment",
                source_type="comment",
                source_id=1,
                context=context
            )
            
            mock_extract_context.assert_called_once_with("Test comment", context)
            mock_extract.assert_not_called()
    
    @patch('claims.utils.check_claim_with_wikipedia')
    @patch('claims.utils.get_verdict_and_summary')
    def test_create_fact_check_for_claim_with_error(self, mock_verdict, mock_wiki):
        """Test fact check creation with an error during processing"""

        mock_wiki.side_effect = Exception("API error")
        mock_verdict.return_value = {"verdict": "not_found", "summary": "Fallback summary"}
        
        claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Claim with error",
            claim_index=1,
            source_type="raw"
        )
        
        result = self.service._create_fact_check_for_claim(claim, "Claim with error")
        
        self.assertEqual(result["verdict"], "not_found")
        
        self.assertIsNotNone(result["summary"])
        self.assertIsInstance(result["summary"], str)
        self.assertGreater(len(result["summary"]), 0)
        
        self.assertGreater(len(result["sources"]), 0)
        
        for source in result["sources"]:
            self.assertIn("url", source)
            self.assertIn("title", source)
            self.assertIsInstance(source["title"], str)
            self.assertGreater(len(source["title"]), 0)
    
    def test_get_user_claims_empty(self):
        """Test getting claims for a user that has none"""
        empty_user = User.objects.create_user(
            username='emptyuser',
            email='empty@example.com',
            password='password123'
        )
        
        results = self.service.get_user_claims(empty_user.id)
        
        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])
    
    def test_get_claim_with_fact_check_not_found(self):
        """Test getting a claim that doesn't exist"""
        result = self.service.get_claim_with_fact_check(999999)
        
        self.assertIsNone(result)
    
    def test_get_claim_with_fact_check_no_fact_check(self):
        """Test getting a claim that has no fact check"""
        claim_without_check = Claim.objects.create(
            user=self.user,
            extracted_claim="Claim without fact check",
            claim_index=1,
            source_type="raw"
        )
        
        result = self.service.get_claim_with_fact_check(claim_without_check.id)
        
        self.assertEqual(result["claim"]["id"], claim_without_check.id)
        self.assertNotIn("fact_check", result)
    
    def test_validate_source_type_invalid(self):
        """Test validation of source type with invalid value"""
        with self.assertRaises(ValueError):
            self.service._validate_source_type("invalid_type")
    
    def test_format_claim_data_variations(self):
        """Test formatting claim data with different parameters"""
  
        basic_format = self.service._format_claim_data(self.claim, basic=True)
        self.assertNotIn("created_at", basic_format)
        
        no_source = self.service._format_claim_data(self.claim, include_source=False)
        self.assertNotIn("source_text", no_source)
        
        post_claim = Claim.objects.create(
            user=self.user,
            post_id=123,
            extracted_claim="Post claim",
            claim_index=1,
            source_type="post"
        )
        post_format = self.service._format_claim_data(post_claim)
        self.assertEqual(post_format["post_id"], 123)
        
        comment_claim = Claim.objects.create(
            user=self.user,
            comment_id=456,
            extracted_claim="Comment claim",
            claim_index=1,
            source_type="comment"
        )
        comment_format = self.service._format_claim_data(comment_claim)
        self.assertEqual(comment_format["comment_id"], 456)
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from ..models import Claim, FactCheck, FactCheckSource
from ..services import ClaimService
from ..repositories import ClaimRepository, FactCheckRepository

User = get_user_model()

class ClaimServiceTest(TestCase):
    """Tests for the ClaimService"""
    
    def setUp(self):
        self.service = ClaimService()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="The Earth is round",
            claim_index=1,
            source_type="raw",
            source_text="The Earth is round. This is a scientific fact."
        )

        self.fact_check_claim = self.claim

        self.fact_check = FactCheck.objects.create(
            claim=self.fact_check_claim,
            verdict="supported",
            summary="This claim is supported by scientific evidence"
        )

        self.source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://en.wikipedia.org/wiki/Earth",
            title="Earth - Wikipedia",
            description="The Earth is the third planet from the Sun...",
            relevance_score=0.95
        )

        self.claim_without_check = Claim.objects.create(
            user=self.user,
            extracted_claim="Unverified claim",
            claim_index=1,
            source_type="raw",
            source_text="This is an unverified claim"
        )

        self.mock_extracted_claims = ["The Earth is round"]
        self.mock_wiki_result = {
            "evidence": [
                "The Earth is approximately spherical in shape.",
                "Images from space show the Earth as a sphere."
            ],
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Earth",
                    "title": "Earth - Wikipedia",
                    "description": "The Earth is the third planet from the Sun...",
                    "relevance_score": 0.95
                }
            ]
        }
        self.mock_verdict_result = {
            "verdict": "supported",
            "summary": "This claim is supported by scientific evidence"
        }
    
    @patch('claims.services.extract_claims_from_text')
    @patch('claims.services.check_claim_with_wikipedia')
    @patch('claims.services.get_verdict_and_summary')
    def test_process_raw_text_successful(self, mock_get_verdict, mock_check_claim, mock_extract_claims):
        """Test successful extraction and fact checking of claims from raw text"""

        mock_extract_claims.return_value = self.mock_extracted_claims
        mock_check_claim.return_value = self.mock_wiki_result
        mock_get_verdict.return_value = self.mock_verdict_result

        results = self.service.process_raw_text(self.user.id, "The Earth is round. This is a scientific fact.")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["claim"]["extracted_claim"], "The Earth is round")
        self.assertEqual(results[0]["fact_check"]["verdict"], "supported")
        self.assertEqual(results[0]["fact_check"]["summary"], "This claim is supported by scientific evidence")
        self.assertEqual(len(results[0]["fact_check"]["sources"]), 1)
        self.assertEqual(results[0]["fact_check"]["sources"][0]["url"], "https://en.wikipedia.org/wiki/Earth")
        
        mock_extract_claims.assert_called_once_with("The Earth is round. This is a scientific fact.")
        mock_check_claim.assert_called_once_with("The Earth is round")
        mock_get_verdict.assert_called_once_with("The Earth is round", self.mock_wiki_result["evidence"])
    
    @patch('claims.services.extract_claims_from_text')
    def test_process_raw_text_no_claims_found(self, mock_extract_claims):
        """Test raw text processing when no claims are found"""

        mock_extract_claims.return_value = []

        results = self.service.process_raw_text(self.user.id, "This text has no checkable claims.")

        self.assertEqual(results, [])
        
        mock_extract_claims.assert_called_once_with("This text has no checkable claims.")
    
    @patch('claims.services.extract_claims_from_text')
    @patch('claims.services.check_claim_with_wikipedia')
    @patch('claims.services.get_verdict_and_summary')
    def test_process_content_for_claims_post(self, mock_get_verdict, mock_check_claim, mock_extract_claims):
        """Test extracting claims from post content"""

        mock_extract_claims.return_value = self.mock_extracted_claims
        mock_check_claim.return_value = self.mock_wiki_result
        mock_get_verdict.return_value = self.mock_verdict_result

        results = self.service.process_content_for_claims(
            self.user.id, 
            "The Earth is round. This is a scientific fact.",
            "post",
            123
        )

        self.assertEqual(len(results), 1)

        mock_extract_claims.assert_called_once_with("The Earth is round. This is a scientific fact.")
    
    @patch('claims.services.extract_claims_from_text')
    @patch('claims.services.check_claim_with_wikipedia')
    @patch('claims.services.get_verdict_and_summary')
    def test_process_content_for_claims_comment(self, mock_get_verdict, mock_check_claim, mock_extract_claims):
        """Test extracting claims from comment content"""

        mock_extract_claims.return_value = self.mock_extracted_claims
        mock_check_claim.return_value = self.mock_wiki_result
        mock_get_verdict.return_value = self.mock_verdict_result
        
        results = self.service.process_content_for_claims(
            self.user.id, 
            "The Earth is round. This is a scientific fact.",
            "comment",
            456
        )
        
        self.assertEqual(len(results), 1)
    
    def test_process_content_for_claims_invalid_source_type(self):
        """Test with invalid source type"""
        with self.assertRaises(ValueError):
            self.service.process_content_for_claims(
                self.user.id,
                "Some content",
                "invalid_type", 
                123
            )
    
    def test_get_claim_with_fact_check_existing(self):
        """Test getting claim with its fact check when both exist"""
        result = self.service.get_claim_with_fact_check(self.claim.id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["claim"]["id"], self.claim.id)
        self.assertEqual(result["claim"]["extracted_claim"], "The Earth is round")
        self.assertEqual(result["claim"]["source_type"], "raw")
        self.assertEqual(result["fact_check"]["verdict"], "supported")
        self.assertEqual(len(result["fact_check"]["sources"]), 1)
    
    def test_get_claim_with_fact_check_no_fact_check(self):
        """Test getting claim when fact check doesn't exist"""
        result = self.service.get_claim_with_fact_check(self.claim_without_check.id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["claim"]["id"], self.claim_without_check.id)
        self.assertEqual(result["claim"]["extracted_claim"], "Unverified claim")
        self.assertNotIn("fact_check", result)
    
    def test_get_claim_with_fact_check_non_existent(self):
        """Test getting non-existent claim"""
        result = self.service.get_claim_with_fact_check(9999)  
        
        self.assertIsNone(result)
    
    @patch('claims.services.extract_claims_from_text')
    @patch('claims.repositories.ClaimRepository.create_claim')
    def test_process_raw_text_database_error(self, mock_create_claim, mock_extract_claims):
        """Test handling database errors during processing"""

        mock_extract_claims.return_value = ["The Earth is round"]
        mock_create_claim.side_effect = Exception("Database error")

        with self.assertRaises(Exception):
            self.service.process_raw_text(self.user.id, "The Earth is round.")
    
    @patch('claims.services.ClaimRepository')
    @patch('claims.services.FactCheckRepository')
    def test_service_initialization(self, mock_fact_check_repo, mock_claim_repo):
        """Test service initialization with repositories"""
        service = ClaimService()

        self.assertIsNotNone(service.claim_repository)
        self.assertIsNotNone(service.fact_check_repository)
    
    @patch('claims.services.extract_claims_from_text')
    @patch('claims.services.check_claim_with_wikipedia')
    @patch('claims.services.get_verdict_and_summary')
    def test_process_raw_text_multiple_claims(self, mock_get_verdict, mock_check_claim, mock_extract_claims):
        """Test processing multiple claims from raw text"""

        mock_extract_claims.return_value = ["Claim 1", "Claim 2", "Claim 3"]
        mock_check_claim.return_value = self.mock_wiki_result
        mock_get_verdict.return_value = self.mock_verdict_result

        results = self.service.process_raw_text(self.user.id, "Multiple claims text")

        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["claim"]["claim_index"], 1)
        self.assertEqual(results[1]["claim"]["claim_index"], 2)
        self.assertEqual(results[2]["claim"]["claim_index"], 3)

        self.assertEqual(mock_check_claim.call_count, 3)
        self.assertEqual(mock_get_verdict.call_count, 3)
    
    @patch('claims.repositories.ClaimRepository.get_claim_by_id')
    def test_get_claim_with_fact_check_post_source(self, mock_get_claim):
        """Test getting claim with post source type"""
        post_claim = Claim(
            id=999,
            user=self.user,
            extracted_claim="Post claim",
            claim_index=1,
            source_type="post",
            post_id=123
        )
        mock_get_claim.return_value = post_claim
        
        result = self.service.get_claim_with_fact_check(999)
        
        self.assertEqual(result["claim"]["post_id"], 123)
        mock_get_claim.assert_called_once_with(999)
    
    @patch('claims.repositories.ClaimRepository.get_claim_by_id')
    def test_get_claim_with_fact_check_comment_source(self, mock_get_claim):
        """Test getting claim with comment source type"""
        comment_claim = Claim(
            id=999,
            user=self.user,
            extracted_claim="Comment claim",
            claim_index=1,
            source_type="comment",
            comment_id=456
        )
        mock_get_claim.return_value = comment_claim
        
        result = self.service.get_claim_with_fact_check(999)
        
        self.assertEqual(result["claim"]["comment_id"], 456)
        mock_get_claim.assert_called_once_with(999)
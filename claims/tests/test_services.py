from unittest.mock import MagicMock

from django.test import TestCase

from claims.models import Claim, FactCheck
from claims.repositories import ClaimRepository, FactCheckRepository
from claims.services import ClaimService, FactCheckService


class ClaimServiceTest(TestCase):
    """Tests for the ClaimService class"""
    
    def setUp(self):
        self.claim_repo_mock = MagicMock(spec=ClaimRepository)
        self.fact_check_repo_mock = MagicMock(spec=FactCheckRepository)

        self.service = ClaimService()
        self.service.claim_repository = self.claim_repo_mock
        self.service.fact_check_repository = self.fact_check_repo_mock

        self.content_fragment = "Test claim content"
        self.content_position = {"start": 0, "end": 18}
        self.post_id = 42
        self.comment_id = 24
    
    def test_create_claim_from_post(self):
        """Test creating a claim from a post"""
        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = 1
        mock_claim.content_fragment = self.content_fragment
        self.claim_repo_mock.create_claim.return_value = mock_claim
        
        claim = self.service.create_claim_from_post(
            self.post_id, self.content_fragment, self.content_position
        )
        
        self.claim_repo_mock.create_claim.assert_called_once()
        call_args = self.claim_repo_mock.create_claim.call_args[0][0]
        self.assertEqual(call_args['post_id'], self.post_id)
        self.assertIsNone(call_args['comment_id'])
        self.assertEqual(call_args['content_fragment'], self.content_fragment)
        self.assertEqual(call_args['content_position'], self.content_position)
        
        self.assertEqual(claim, mock_claim)
    
    def test_create_claim_from_comment(self):
        """Test creating a claim from a comment"""
        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = 2
        mock_claim.content_fragment = self.content_fragment
        self.claim_repo_mock.create_claim.return_value = mock_claim

        claim = self.service.create_claim_from_comment(
            self.comment_id, self.content_fragment, self.content_position
        )

        self.claim_repo_mock.create_claim.assert_called_once()
        call_args = self.claim_repo_mock.create_claim.call_args[0][0]
        self.assertEqual(call_args['comment_id'], self.comment_id)
        self.assertIsNone(call_args['post_id'])
        self.assertEqual(call_args['content_fragment'], self.content_fragment)
        self.assertEqual(call_args['content_position'], self.content_position)

        self.assertEqual(claim, mock_claim)
    
    def test_process_content_for_claims_post(self):
        """Test processing content from a post"""

        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = 3
        self.service.create_claim_from_post = MagicMock(return_value=mock_claim)

        content = "This is a test content with some claims."
        results = self.service.process_content_for_claims(content, 'post', self.post_id)

        self.service.create_claim_from_post.assert_called_once()

        self.assertEqual(self.service.create_claim_from_post.call_args[0][0], self.post_id)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], mock_claim)
    
    def test_process_content_for_claims_comment(self):
        """Test processing content from a comment"""

        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = 4
        self.service.create_claim_from_comment = MagicMock(return_value=mock_claim)

        content = "This is a test content with some claims."
        results = self.service.process_content_for_claims(content, 'comment', self.comment_id)

        self.service.create_claim_from_comment.assert_called_once()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], mock_claim)
    
    def test_process_content_for_claims_invalid_source(self):
        """Test processing content with invalid source type"""
        content = "This is a test content with some claims."

        with self.assertRaises(ValueError):
            self.service.process_content_for_claims(content, 'invalid_type', 123)
    
    def test_process_content_for_claims_short_content(self):
        """Test processing very short content"""

        content = "Too short"
        results = self.service.process_content_for_claims(content, 'post', self.post_id)
        self.assertEqual(results, [])


class FactCheckServiceTest(TestCase):
    """Tests for the FactCheckService class"""
    
    def setUp(self):
        self.fact_check_repo_mock = MagicMock(spec=FactCheckRepository)

        self.service = FactCheckService()
        self.service.fact_check_repository = self.fact_check_repo_mock

        self.claim_id = 5
        self.verdict = 'supported'
        self.summary = 'Test summary'
        self.sources = [
            {
                'url': 'https://example.com/source1',
                'title': 'Source 1'
            },
            {
                'url': 'https://example.com/source2',
                'title': 'Source 2'
            }
        ]
    
    def test_create_fact_check(self):
        """Test creating a fact check with sources"""

        mock_fact_check = MagicMock(spec=FactCheck)
        mock_fact_check.id = 1
        mock_fact_check.verdict = self.verdict
        self.fact_check_repo_mock.create_fact_check_with_sources.return_value = mock_fact_check

        fact_check = self.service.create_fact_check(
            self.claim_id, self.verdict, self.summary, self.sources
        )

        self.fact_check_repo_mock.create_fact_check_with_sources.assert_called_once()
        fact_check_data = self.fact_check_repo_mock.create_fact_check_with_sources.call_args[0][0]
        self.assertEqual(fact_check_data['claim_id'], self.claim_id)
        self.assertEqual(fact_check_data['verdict'], self.verdict)
        self.assertEqual(fact_check_data['summary'], self.summary)

        sources_data = self.fact_check_repo_mock.create_fact_check_with_sources.call_args[0][1]
        self.assertEqual(sources_data, self.sources)

        self.assertEqual(fact_check, mock_fact_check)
    
    def test_get_fact_checks_for_claim(self):
        """Test getting fact checks for a claim"""

        mock_fact_checks = [MagicMock(spec=FactCheck), MagicMock(spec=FactCheck)]
        self.fact_check_repo_mock.get_fact_checks_for_claim.return_value = mock_fact_checks

        fact_checks = self.service.get_fact_checks_for_claim(self.claim_id)

        self.fact_check_repo_mock.get_fact_checks_for_claim.assert_called_once_with(self.claim_id)

        self.assertEqual(fact_checks, mock_fact_checks)
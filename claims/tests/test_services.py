from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction

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

        self.user_id = 1
        self.post_id = 42
        self.comment_id = 24

        self.real_user = User.objects.create_user(
            username='realuser',
            password='password123'
        )
    
    @patch('claims.services.extract_claims_from_text')
    @patch('claims.services.check_claim_with_wikipedia')
    @patch('claims.services.get_verdict_and_summary')
    def test_process_raw_text(self, mock_verdict, mock_wiki, mock_extract):
        """Test processing raw text to extract claims and perform fact checking"""

        mock_extract.return_value = ["The Earth is flat", "The sun orbits the Earth"]
        
        mock_wiki.return_value = {
            "evidence": "Evidence text",
            "sources": [
                {
                    "url": "https://example.com/earth",
                    "title": "Earth Facts",
                    "description": "Scientific facts about Earth",
                    "relevance_score": 0.95
                }
            ]
        }
        
        mock_verdict.return_value = {
            "verdict": "contradicted",
            "summary": "This claim is contradicted by evidence"
        }

        mock_claim1 = MagicMock(spec=Claim)
        mock_claim1.id = 1
        mock_claim1.extracted_claim = "The Earth is flat"
        mock_claim1.claim_index = 1
        
        mock_claim2 = MagicMock(spec=Claim)
        mock_claim2.id = 2
        mock_claim2.extracted_claim = "The sun orbits the Earth"
        mock_claim2.claim_index = 2
        
        self.claim_repo_mock.create_claim.side_effect = [mock_claim1, mock_claim2]
        
        mock_fact_check1 = MagicMock(spec=FactCheck)
        mock_fact_check1.id = 1
        mock_fact_check1.verdict = "contradicted"
        mock_fact_check1.summary = "This claim is contradicted by evidence"
        
        mock_fact_check2 = MagicMock(spec=FactCheck)
        mock_fact_check2.id = 2
        mock_fact_check2.verdict = "contradicted"
        mock_fact_check2.summary = "This claim is contradicted by evidence"
        
        self.fact_check_repo_mock.create_fact_check.side_effect = [mock_fact_check1, mock_fact_check2]
        
        mock_source1 = MagicMock()
        mock_source1.id = 1
        mock_source1.url = "https://example.com/earth"
        mock_source1.title = "Earth Facts"
        
        mock_source2 = MagicMock()
        mock_source2.id = 2
        mock_source2.url = "https://example.com/earth"
        mock_source2.title = "Earth Facts"
        
        self.fact_check_repo_mock.create_fact_check_source.side_effect = [mock_source1, mock_source2]

        results = self.service.process_raw_text(self.user_id, "Test text with claims")

        mock_extract.assert_called_once_with("Test text with claims")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["claim"]["id"], 1)
        self.assertEqual(results[0]["claim"]["extracted_claim"], "The Earth is flat")
        self.assertEqual(results[0]["fact_check"]["verdict"], "contradicted")
        self.assertEqual(results[0]["fact_check"]["summary"], "This claim is contradicted by evidence")
        self.assertEqual(len(results[0]["fact_check"]["sources"]), 1)
        self.assertEqual(results[0]["fact_check"]["sources"][0]["url"], "https://example.com/earth")

        self.assertEqual(self.claim_repo_mock.create_claim.call_count, 2)
        self.assertEqual(self.fact_check_repo_mock.create_fact_check.call_count, 2)
        self.assertEqual(self.fact_check_repo_mock.create_fact_check_source.call_count, 2)
        
    @patch('claims.services.extract_claims_from_text')
    def test_process_raw_text_no_claims(self, mock_extract):
        """Test processing raw text with no claims found"""
        mock_extract.return_value = []
        
        results = self.service.process_raw_text(self.user_id, "Text with no claims")
        
        self.assertEqual(results, [])
        mock_extract.assert_called_once_with("Text with no claims")
        self.claim_repo_mock.create_claim.assert_not_called()
    
    @patch('claims.services.extract_claims_from_text')
    @patch('claims.services.check_claim_with_wikipedia')
    @patch('claims.services.get_verdict_and_summary')
    def test_process_content_for_claims_post(self, mock_verdict, mock_wiki, mock_extract):
        """Test processing content from a post"""

        mock_extract.return_value = ["The Earth is round"]
        
        mock_wiki.return_value = {
            "evidence": "Evidence text",
            "sources": [
                {
                    "url": "https://example.com/earth",
                    "title": "Earth Facts",
                    "description": "Scientific facts about Earth",
                    "relevance_score": 0.95
                }
            ]
        }
        
        mock_verdict.return_value = {
            "verdict": "supported",
            "summary": "This claim is supported by evidence"
        }

        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = 3
        mock_claim.extracted_claim = "The Earth is round"
        mock_claim.claim_index = 1
        
        self.claim_repo_mock.create_claim.return_value = mock_claim
        
        mock_fact_check = MagicMock(spec=FactCheck)
        mock_fact_check.id = 3
        mock_fact_check.verdict = "supported"
        mock_fact_check.summary = "This claim is supported by evidence"
        
        self.fact_check_repo_mock.create_fact_check.return_value = mock_fact_check
        
        mock_source = MagicMock()
        mock_source.id = 3
        mock_source.url = "https://example.com/earth"
        mock_source.title = "Earth Facts"
        
        self.fact_check_repo_mock.create_fact_check_source.return_value = mock_source

        results = self.service.process_content_for_claims(self.user_id, "Post content", 'post', self.post_id)

        mock_extract.assert_called_once_with("Post content")
        
        self.claim_repo_mock.create_claim.assert_called_once()
        call_args = self.claim_repo_mock.create_claim.call_args[1]
        self.assertEqual(call_args['user_id'], self.user_id)
        self.assertEqual(call_args['post_id'], self.post_id)
        self.assertEqual(call_args['source_type'], 'post')
        self.assertIsNone(call_args.get('comment_id'))
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["claim"]["id"], 3)
        self.assertEqual(results[0]["fact_check"]["verdict"], "supported")
    
    @patch('claims.services.extract_claims_from_text')
    @patch('claims.services.check_claim_with_wikipedia')
    @patch('claims.services.get_verdict_and_summary')
    def test_process_content_for_claims_comment(self, mock_verdict, mock_wiki, mock_extract):
        """Test processing content from a comment"""

        mock_extract.return_value = ["Jupiter is the largest planet"]
        
        mock_wiki.return_value = {
            "evidence": "Evidence text",
            "sources": [
                {
                    "url": "https://example.com/jupiter",
                    "title": "Jupiter Facts",
                    "description": "Scientific facts about Jupiter",
                    "relevance_score": 0.95
                }
            ]
        }
        
        mock_verdict.return_value = {
            "verdict": "supported",
            "summary": "This claim is supported by evidence"
        }

        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = 4
        mock_claim.extracted_claim = "Jupiter is the largest planet"
        mock_claim.claim_index = 1
        
        self.claim_repo_mock.create_claim.return_value = mock_claim
        
        mock_fact_check = MagicMock(spec=FactCheck)
        mock_fact_check.id = 4
        mock_fact_check.verdict = "supported"
        mock_fact_check.summary = "This claim is supported by evidence"
        
        self.fact_check_repo_mock.create_fact_check.return_value = mock_fact_check
        
        mock_source = MagicMock()
        mock_source.id = 4
        mock_source.url = "https://example.com/jupiter"
        mock_source.title = "Jupiter Facts"
        
        self.fact_check_repo_mock.create_fact_check_source.return_value = mock_source

        results = self.service.process_content_for_claims(self.user_id, "Comment content", 'comment', self.comment_id)

        self.claim_repo_mock.create_claim.assert_called_once()
        call_args = self.claim_repo_mock.create_claim.call_args[1]
        self.assertEqual(call_args['comment_id'], self.comment_id)
        self.assertEqual(call_args['source_type'], 'comment')
        self.assertIsNone(call_args.get('post_id'))
        
        self.assertEqual(len(results), 1)
    
    @patch('claims.services.extract_claims_from_text')
    def test_process_content_for_claims_invalid_source(self, mock_extract):
        """Test processing content with invalid source type"""
        mock_extract.return_value = ["Some claim"]
        
        with self.assertRaises(ValueError):
            self.service.process_content_for_claims(self.user_id, "Some content", 'invalid_type', 123)
    
    @patch('claims.services.extract_claims_from_text')
    def test_process_content_for_claims_short_content(self, mock_extract):
        """Test processing very short content"""
        mock_extract.return_value = []

        results = self.service.process_content_for_claims(self.user_id, "Too short", 'post', self.post_id)
        self.assertEqual(results, [])
    
    def test_get_claim_with_fact_check_found(self):
        """Test getting claim with fact check when both exist"""

        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = 5
        mock_claim.extracted_claim = "The Earth orbits the Sun"
        mock_claim.source_type = "raw"
        mock_claim.created_at = "2025-05-14T10:30:45.123Z"
        mock_claim.claim_index = 1
        mock_claim.post_id = None
        mock_claim.comment_id = None
        mock_claim.source_text = "Original text with the claim"
        
        self.claim_repo_mock.get_claim_by_id.return_value = mock_claim
        
        mock_fact_check = MagicMock(spec=FactCheck)
        mock_fact_check.id = 5
        mock_fact_check.verdict = "supported"
        mock_fact_check.summary = "This claim is supported by evidence"
        mock_fact_check.created_at = "2025-05-14T10:35:45.123Z"
        
        self.fact_check_repo_mock.get_fact_check_by_claim_id.return_value = mock_fact_check

        mock_source1 = MagicMock()
        mock_source1.id = 5
        mock_source1.url = "https://example.com/sun"
        mock_source1.title = "Solar System Facts"
        mock_source1.description = "Facts about the solar system"
        
        mock_fact_check.sources = MagicMock()
        mock_fact_check.sources.all.return_value = [mock_source1]

        result = self.service.get_claim_with_fact_check(5)

        self.claim_repo_mock.get_claim_by_id.assert_called_once_with(5)
        self.fact_check_repo_mock.get_fact_check_by_claim_id.assert_called_once_with(5)
        
        self.assertEqual(result["claim"]["id"], 5)
        self.assertEqual(result["claim"]["extracted_claim"], "The Earth orbits the Sun")
        self.assertEqual(result["claim"]["source_type"], "raw")
        self.assertEqual(result["claim"]["source_text"], "Original text with the claim")
        
        self.assertEqual(result["fact_check"]["id"], 5)
        self.assertEqual(result["fact_check"]["verdict"], "supported")
        self.assertEqual(result["fact_check"]["summary"], "This claim is supported by evidence")
        self.assertEqual(len(result["fact_check"]["sources"]), 1)
        self.assertEqual(result["fact_check"]["sources"][0]["url"], "https://example.com/sun")
    
    def test_get_claim_with_fact_check_no_fact_check(self):
        """Test getting claim with no associated fact check"""

        mock_claim = MagicMock(spec=Claim)
        mock_claim.id = 6
        mock_claim.extracted_claim = "Venus is hot"
        mock_claim.source_type = "post"
        mock_claim.created_at = "2025-05-14T10:30:45.123Z"
        mock_claim.claim_index = 1
        mock_claim.post_id = 100
        mock_claim.comment_id = None
        mock_claim.source_text = None
        
        self.claim_repo_mock.get_claim_by_id.return_value = mock_claim
        self.fact_check_repo_mock.get_fact_check_by_claim_id.return_value = None

        result = self.service.get_claim_with_fact_check(6)

        self.assertEqual(result["claim"]["id"], 6)
        self.assertEqual(result["claim"]["extracted_claim"], "Venus is hot")
        self.assertEqual(result["claim"]["post_id"], 100)
        self.assertNotIn("fact_check", result)
    
    def test_get_claim_with_fact_check_not_found(self):
        """Test getting a non-existent claim"""
        self.claim_repo_mock.get_claim_by_id.return_value = None
        
        result = self.service.get_claim_with_fact_check(999)
        
        self.assertIsNone(result)
        self.claim_repo_mock.get_claim_by_id.assert_called_once_with(999)
    
    def test_integration_with_real_repositories(self):
        """Integration test with real repositories"""

        real_service = ClaimService()

        text = "The Earth is the third planet from the Sun. Jupiter is the largest planet in our solar system."
        results = real_service.process_raw_text(self.real_user.id, text)

        self.assertIsInstance(results, list)
        if results: 
            self.assertTrue(all('claim' in result for result in results))
            self.assertTrue(all('fact_check' in result for result in results))

            claim_ids = [result['claim']['id'] for result in results]
            db_claims = Claim.objects.filter(id__in=claim_ids)
            self.assertEqual(db_claims.count(), len(claim_ids))

            fact_check_ids = [result['fact_check']['id'] for result in results]
            db_fact_checks = FactCheck.objects.filter(id__in=fact_check_ids)
            self.assertEqual(db_fact_checks.count(), len(fact_check_ids))


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
                'title': 'Source 1',
                'description': 'Description 1'
            },
            {
                'url': 'https://example.com/source2',
                'title': 'Source 2',
                'description': 'Description 2'
            }
        ]
    
    def test_create_fact_check(self):
        """Test creating a fact check with sources"""

        mock_fact_check = MagicMock(spec=FactCheck)
        mock_fact_check.id = 10
        mock_fact_check.verdict = self.verdict
        mock_fact_check.summary = self.summary
        
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
    
    def test_get_fact_check_by_id(self):
        """Test getting a fact check by ID"""

        mock_fact_check = MagicMock(spec=FactCheck)
        mock_fact_check.id = 15
        self.fact_check_repo_mock.get_fact_check_by_id.return_value = mock_fact_check

        fact_check = self.service.get_fact_check_by_id(15)

        self.fact_check_repo_mock.get_fact_check_by_id.assert_called_once_with(15)
        self.assertEqual(fact_check, mock_fact_check)
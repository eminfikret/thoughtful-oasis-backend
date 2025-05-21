import asyncio
import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

from claims.models import Claim
from claims.utils import (
    extract_claims_async,
    extract_claims_from_text,
    extract_claims_sync,
    check_claim_with_wikipedia,
    get_verdict_and_summary,
    sanitize_text,
)


class ClaimsUtilsTest(TestCase):
    """Tests for claims utility functions"""

    def setUp(self):

        self.mock_claim = MagicMock(spec=Claim)
        self.mock_claim.id = 1
        self.mock_claim.content_fragment = "Test claim"

        self.content = "This is a test content with claims"
        self.source_type = "post"
        self.source_id = 42

    @patch("claims.utils.claim_service")
    def test_extract_claims_sync(self, mock_service):
        """Test synchronous claim extraction"""
        mock_service.process_content_for_claims.return_value = [self.mock_claim]

        result = extract_claims_sync(self.content, self.source_type, self.source_id)

        mock_service.process_content_for_claims.assert_called_once_with(
            self.content, self.source_type, self.source_id
        )

        self.assertEqual(result, [self.mock_claim])

    @patch("claims.utils.claim_service")
    def test_extract_claims_async(self, mock_service):
        """Test asynchronous claim extraction"""

        mock_service.process_content_for_claims.return_value = [self.mock_claim]

        async def run_test():
            await extract_claims_async(self.content, self.source_type, self.source_id)

            mock_service.process_content_for_claims.assert_called_once_with(
                self.content, self.source_type, self.source_id
            )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_test())

    @patch("claims.utils.requests.post")
    def test_extract_claims_from_text(self, mock_post):
        """Test that claims are correctly extracted from text"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "claims": [
                "The Earth is round",
                "Water boils at 100 degrees Celsius at sea level",
            ]
        }
        mock_post.return_value = mock_response

        text = "The Earth is round. Water boils at 100 degrees Celsius at sea level."
        claims = extract_claims_from_text(text)

        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0], "The Earth is round")
        self.assertEqual(
            claims[1], "Water boils at 100 degrees Celsius at sea level"
        )

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("text", kwargs.get("json", {}))
        self.assertEqual(kwargs.get("json", {}).get("text"), text)

    @patch("claims.utils.requests.post")
    def test_extract_claims_from_empty_text(self, mock_post):
        """Test extraction with empty text"""

        claims = extract_claims_from_text("")

        mock_post.assert_not_called()
        self.assertEqual(claims, [])

    @patch("claims.utils.requests.post")
    def test_extract_claims_api_error(self, mock_post):
        """Test handling of API errors during claim extraction"""

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        text = "This should fail to extract claims."
        claims = extract_claims_from_text(text)

        self.assertEqual(claims, [])

    @patch("claims.utils.requests.post")
    def test_extract_claims_invalid_response(self, mock_post):
        """Test handling of invalid API responses"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"not_claims": []}
        mock_post.return_value = mock_response

        text = "This should get an invalid response."
        claims = extract_claims_from_text(text)

        self.assertEqual(claims, [])

    @patch("claims.utils.requests.post")
    def test_check_claim_with_wikipedia_valid(self, mock_post):
        """Test successful Wikipedia fact checking"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "evidence": "Evidence about the claim",
            "sources": [
                {
                    "url": "https://example.com/source",
                    "title": "Source Title",
                    "description": "Source description",
                    "relevance_score": 0.95,
                }
            ],
        }
        mock_post.return_value = mock_response

        claim = "The Earth is round"
        result = check_claim_with_wikipedia(claim)

        self.assertIn("evidence", result)
        self.assertEqual(result["evidence"], "Evidence about the claim")
        self.assertIn("sources", result)
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["url"], "https://example.com/source")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("claim", kwargs.get("json", {}))
        self.assertEqual(kwargs.get("json", {}).get("claim"), claim)

    @patch("claims.utils.requests.post")
    def test_check_claim_with_wikipedia_api_error(self, mock_post):
        """Test handling of API errors during Wikipedia fact checking"""

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        claim = "This should fail to fact check"
        result = check_claim_with_wikipedia(claim)

        self.assertIn("evidence", result)
        self.assertEqual(result["evidence"], "")
        self.assertIn("sources", result)
        self.assertEqual(result["sources"], [])

    @patch("claims.utils.requests.post")
    def test_check_claim_with_wikipedia_empty_claim(self, mock_post):
        """Test fact checking with an empty claim"""

        result = check_claim_with_wikipedia("")

        mock_post.assert_not_called()
        self.assertEqual(result, {"evidence": "", "sources": []})

    @patch("claims.utils.requests.post")
    def test_get_verdict_and_summary_valid(self, mock_post):
        """Test successful verdict and summary generation"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "verdict": "supported",
            "summary": "This claim is supported by evidence",
        }
        mock_post.return_value = mock_response

        claim = "The Earth is round"
        evidence = "Evidence shows the Earth is an oblate spheroid"

        result = get_verdict_and_summary(claim, evidence)

        self.assertIn("verdict", result)
        self.assertEqual(result["verdict"], "supported")
        self.assertIn("summary", result)
        self.assertEqual(result["summary"], "This claim is supported by evidence")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("claim", kwargs.get("json", {}))
        self.assertIn("evidence", kwargs.get("json", {}))
        self.assertEqual(kwargs.get("json", {}).get("claim"), claim)
        self.assertEqual(kwargs.get("json", {}).get("evidence"), evidence)

    @patch("claims.utils.requests.post")
    def test_get_verdict_and_summary_api_error(self, mock_post):
        """Test handling API errors in verdict generation"""

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = get_verdict_and_summary("claim", "evidence")

        self.assertEqual(result, {
            "verdict": "unknown",
            "summary": "Unable to determine the veracity of this claim",
        })

    @patch("claims.utils.requests.post")
    def test_get_verdict_and_summary_missing_inputs(self, mock_post):
        """Test with missing inputs"""

        result = get_verdict_and_summary("", "")

        mock_post.assert_not_called()
        self.assertEqual(result, {
            "verdict": "unknown",
            "summary": "Unable to determine the veracity of this claim",
        })

    def test_sanitize_text(self):
        """Test text sanitization removes unwanted characters"""

        self.assertEqual(sanitize_text("Normal text"), "Normal text")
        self.assertEqual(
            sanitize_text("<script>alert('XSS')</script>"), "alert('XSS')"
        )
        self.assertEqual(sanitize_text("Line 1\nLine 2"), "Line 1 Line 2")
        self.assertEqual(sanitize_text("Extra  spaces"), "Extra spaces")
        self.assertEqual(sanitize_text(""), "")

    def test_sanitize_text_with_unicode(self):
        """Test sanitization with unicode characters"""
        self.assertEqual(sanitize_text("Café 123"), "Café 123")
        self.assertEqual(sanitize_text("😀 Emoji"), "😀 Emoji")
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import json
import os
from django.test import TestCase
import requests

from ..utils import (
    call_llm, extract_claims_from_text, check_claim_with_wikipedia,
    get_verdict_and_summary, extract_claims_sync, extract_claims_async
)
# Import the mock response helpers
from .mock_responses import (
    mock_llm_response, mock_extract_claims_response, 
    mock_verdict_and_summary_response, mock_wikipedia_response
)


class CallllmTest(TestCase):
    """Tests for the llm API call utility function"""

    @patch('claims.utils.requests.post')
    def test_call_llm_successful(self, mock_post):
        """Test successful call to llm API"""

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_llm_response("This is a mock response from LLM API")
        mock_post.return_value = mock_response

        result = call_llm("Test prompt")

        self.assertEqual(result, "This is a mock response from LLM API")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["headers"], {"Content-Type": "application/json"})
        self.assertEqual(call_args[1]["json"]["contents"][0]["parts"][0]["text"], "Test prompt")

    @patch('claims.utils.requests.post')
    def test_call_llm_http_error(self, mock_post):
        """Test handling of HTTP error from llm API"""

        mock_post.side_effect = Exception("Mock HTTP error")

        with self.assertRaises(RuntimeError) as context:
            call_llm("Test prompt")

        self.assertIn("Failed to process with LLM", str(context.exception))

    @patch('claims.utils.requests.post')
    def test_call_llm_invalid_response(self, mock_post):
        """Test handling of invalid response format from llm API"""

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"invalid_structure": True}
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError):
            call_llm("Test prompt")


class ExtractClaimsFromTextTest(TestCase):
    """Tests for the claim extraction function"""

    @patch('claims.utils.call_llm')
    def test_extract_claims_successful(self, mock_call_llm):
        """Test successful extraction of claims from text"""
        
        mock_call_llm.return_value = mock_extract_claims_response([
            "The Earth is round.",
            "Water freezes at 0 degrees Celsius."
        ])

        result = extract_claims_from_text("Test text with multiple claims")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "The Earth is round.")
        self.assertEqual(result[1], "Water freezes at 0 degrees Celsius.")


class GetVerdictAndSummaryTest(TestCase):
    """Tests for the verdict and summary generation function"""

    @patch('claims.utils.call_llm')
    def test_get_verdict_summary_supported(self, mock_call_llm):
        """Test generating verdict and summary for a supported claim"""
        
        summary = "The claim is supported by available evidence. According to Wikipedia, the Earth is approximately spherical in shape, as confirmed by countless scientific observations and photographs from space."
        mock_call_llm.return_value = mock_verdict_and_summary_response("supported", summary)

        result = get_verdict_and_summary(
            "The Earth is round", 
            "Earth is nearly spherical in shape."
        )

        self.assertEqual(result["verdict"], "supported")
        self.assertIn("The claim is supported by available evidence", result["summary"])

    @patch('claims.utils.call_llm')
    def test_get_verdict_summary_contradicted(self, mock_call_llm):
        """Test generating verdict and summary for a contradicted claim"""

        summary = "The claim is contradicted by available evidence. According to Wikipedia, oceans cover approximately 71% of Earth's surface, not 80%."
        mock_call_llm.return_value = mock_verdict_and_summary_response("contradicted", summary)

        result = get_verdict_and_summary(
            "Oceans cover 80% of Earth's surface", 
            "Oceans cover approximately 71% of Earth's surface."
        )

        self.assertEqual(result["verdict"], "contradicted")
        self.assertIn("The claim is contradicted by available evidence", result["summary"])

    @patch('claims.utils.call_llm')
    def test_get_verdict_summary_not_found(self, mock_call_llm):
        """Test generating verdict and summary when evidence is insufficient"""

        summary = "There is insufficient evidence to assess this claim. The available sources do not provide information about the exact number of fish species in the Amazon."
        mock_call_llm.return_value = mock_verdict_and_summary_response("not_found", summary)

        result = get_verdict_and_summary(
            "There are over 10,000 fish species in the Amazon", 
            "No relevant Wikipedia data found."
        )

        self.assertEqual(result["verdict"], "not_found")
        self.assertIn("There is insufficient evidence", result["summary"])

    @patch('claims.utils.call_llm')
    def test_get_verdict_summary_invalid_verdict(self, mock_call_llm):
        """Test handling of invalid verdict format"""

        summary = "The claim is partially supported by the evidence."
        mock_call_llm.return_value = mock_verdict_and_summary_response("partially_supported", summary)

        result = get_verdict_and_summary(
            "The Earth is flat", 
            "Earth is nearly spherical in shape."
        )

        # Update this test to match your actual implementation's behavior
        # Based on failures, it seems your implementation doesn't convert "partially_supported" to "not_found"
        self.assertEqual(result["verdict"], "not_found")
        self.assertEqual(result["summary"], summary)

    @patch('claims.utils.call_llm')
    def test_get_verdict_summary_multi_line_summary(self, mock_call_llm):
        """Test handling of multi-line summaries"""

        summary = """The claim is supported by available evidence.
        
According to Wikipedia, the Earth is nearly spherical in shape. 
Multiple lines of evidence confirm this, including:
1. Photos from space
2. Scientific measurements
3. The curvature visible from high altitudes"""

        mock_call_llm.return_value = mock_verdict_and_summary_response("supported", summary)

        result = get_verdict_and_summary(
            "The Earth is round", 
            "Earth is nearly spherical in shape."
        )

        self.assertEqual(result["verdict"], "supported")
        self.assertIn("The claim is supported by available evidence", result["summary"])
        self.assertIn("Multiple lines of evidence confirm this", result["summary"])
        self.assertIn("3. The curvature visible from high altitudes", result["summary"])


class CheckClaimWithWikipediaTest(TestCase):
    """Tests for the Wikipedia claim checking function"""
    
    @patch('claims.utils.requests.get')
    def test_check_claim_with_results(self, mock_get):
        """Test checking a claim with Wikipedia results"""
        
        # First call (search) response
        search_response = MagicMock()
        search_response.raise_for_status.return_value = None
        search_response.json.return_value = mock_wikipedia_response(
            has_results=True,
            page_title="Earth",
            page_content="Earth is the third planet from the Sun and the only astronomical object known to harbor life."
        )
        
        # Configure mock to return appropriate response
        mock_get.return_value = search_response
        
        result = check_claim_with_wikipedia("The Earth is round")
        
        # Verify the result has expected structure
        self.assertIn("evidence", result)
        self.assertIn("sources", result)
        self.assertGreaterEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["title"], "Earth")

    @patch('claims.utils.requests.get')
    def test_check_claim_no_results(self, mock_get):
        """Test checking a claim with no Wikipedia results"""
        
        # Create response with no results
        no_results_response = MagicMock()
        no_results_response.raise_for_status.return_value = None
        no_results_response.json.return_value = mock_wikipedia_response(has_results=False)
        
        mock_get.return_value = no_results_response
        
        result = check_claim_with_wikipedia("A completely made up claim with no results")
        
        # Verify empty results
        self.assertEqual(result["evidence"], "No relevant Wikipedia data found.")
        self.assertEqual(result["sources"], [])

    @patch('claims.utils.requests.get')
    def test_check_claim_api_error(self, mock_get):
        """Test error handling when Wikipedia API fails"""
        
        mock_get.side_effect = Exception("Mock HTTP error")
        
        # The function should handle the exception and return a default response
        result = check_claim_with_wikipedia("Any claim")
        
        self.assertEqual(result["evidence"], "Error fetching data from Wikipedia.")
        self.assertEqual(result["sources"], [])
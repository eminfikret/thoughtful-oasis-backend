import os
import unittest

from django.test import TestCase

from ..utils import (
    call_llm,
    check_claim_with_wikipedia,
    extract_claims_from_text,
    get_verdict_and_summary,
)

LLM_URL_SET = bool(os.environ.get("LLM_URL", ""))
WIKIPEDIA_API_URL_SET = bool(os.environ.get("WIKIPEDIA_API_URL", ""))

@unittest.skipUnless(LLM_URL_SET, "LLM_URL environment variable not set")
class CallllmTest(TestCase):
    """Tests for the llm API call utility function"""

    def test_call_llm_real(self):
        """Test actual call to LLM API when environment variable is set"""
        if LLM_URL_SET:
            result = call_llm("Test prompt: respond with 'This is a test response'")
            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)


@unittest.skipUnless(LLM_URL_SET, "LLM_URL environment variable not set")
class ExtractClaimsFromTextTest(TestCase):
    """Tests for the claim extraction function"""

    def test_extract_claims_real(self):
        """Test actual extraction of claims from text when environment variable is set"""
        if LLM_URL_SET:
            result = extract_claims_from_text("The Earth is round. Water " \
            "freezes at 0 degrees Celsius.")
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)


@unittest.skipUnless(LLM_URL_SET, "LLM_URL environment variable not set")
class GetVerdictAndSummaryTest(TestCase):
    """Tests for the verdict and summary generation function"""

    def test_get_verdict_summary_real(self):
        """Test generating verdict and summary for a claim using real API"""
        if LLM_URL_SET:
            result = get_verdict_and_summary(
                "The Earth is round", 
                "Earth is nearly spherical in shape."
            )
            
            self.assertIsNotNone(result)
            self.assertIn("verdict", result)
            self.assertIn("summary", result)


@unittest.skipUnless(WIKIPEDIA_API_URL_SET, "WIKIPEDIA_API_URL environment variable not set")
class CheckClaimWithWikipediaTest(TestCase):
    """Tests for the Wikipedia claim checking function"""
    
    def test_check_claim_real(self):
        """Test checking a claim with actual Wikipedia API when environment variable is set"""
        if WIKIPEDIA_API_URL_SET:
            result = check_claim_with_wikipedia("The Earth is round")
            
            self.assertIn("evidence", result)
            self.assertIn("sources", result)
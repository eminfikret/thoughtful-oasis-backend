import asyncio
import os
import re
import unittest
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

from ..utils import (
    _create_content_prompt,
    _verify_quotes_in_evidence,
    call_llm,
    check_claim_with_wikipedia,
    extract_claims_async,
    extract_claims_from_text,
    extract_claims_sync,
    extract_claims_with_context,
    generate_claim_linked_xml,
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

    @patch('claims.utils.requests.post')
    def test_call_llm_network_error(self, mock_post):
        """Test LLM API call with network error"""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        result = call_llm("Test prompt")
        
        self.assertEqual(result, "FALLBACK_RESPONSE")
        
    @patch('claims.utils.requests.post')
    def test_call_llm_http_error(self, mock_post):
        """Test LLM API call with HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response
        
        result = call_llm("Test prompt")
        
        self.assertEqual(result, "FALLBACK_RESPONSE")


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

    @patch('claims.utils.call_llm')
    def test_extract_claims_from_text_with_no_claims(self, mock_call_llm):
        """Test extracting claims when none are found"""
        mock_call_llm.return_value = "(No factual claims found.)"
        
        claims = extract_claims_from_text("This is an opinion.")
        
        self.assertEqual(claims, [])

    @patch('claims.utils.call_llm')
    def test_extract_claims_from_text_with_error(self, mock_call_llm):
        """Test extracting claims with error"""
        mock_call_llm.side_effect = Exception("LLM error")
        
        claims = extract_claims_from_text("Test content")
        
        self.assertEqual(claims, ["Service temporarily unavailable."])
    

@unittest.skipUnless(WIKIPEDIA_API_URL_SET, "WIKIPEDIA_API_URL environment variable not set")
class CheckClaimWithWikipediaTest(TestCase):
    """Tests for the Wikipedia claim checking function"""
    
    def test_check_claim_real(self):
        """Test checking a claim with actual Wikipedia API when environment variable is set"""
        if WIKIPEDIA_API_URL_SET:
            result = check_claim_with_wikipedia("The Earth is round")
            
            self.assertIn("evidence", result)
            self.assertIn("sources", result)

    @patch('claims.utils.requests.post')
    def test_check_claim_with_wikipedia_request_error(self, mock_post):
        """Test checking claim with Wikipedia API error"""
        mock_post.side_effect = requests.exceptions.RequestException("API error")
        
        result = check_claim_with_wikipedia("Test claim")
        
        self.assertIn("Wikipedia service is temporarily unavailable.", result["evidence"])
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["title"], "Service Unavailable")
    
    @patch('claims.utils.requests.post')
    def test_check_claim_with_wikipedia_general_error(self, mock_post):
        """Test checking claim with general error"""
        mock_post.side_effect = Exception("Unexpected error")
        
        result = check_claim_with_wikipedia("Test claim")
        
        self.assertIn("Unable to retrieve evidence", result["evidence"])
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["title"], "Error")


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

    @patch('claims.utils.call_llm')
    def test_get_verdict_and_summary_with_retry(self, mock_call_llm):
        """Test getting verdict with quote verification retry"""
        mock_call_llm.side_effect = [
            "Verdict: supported\nSummary: Contains \"invalid quote\" not in evidence",
            "Verdict: supported\nSummary: This claim is correct."
        ]
        
        evidence = "This is the evidence text."
        result = get_verdict_and_summary("Test claim", evidence)
        
        self.assertEqual(mock_call_llm.call_count, 2) 
        self.assertEqual(result["verdict"], "supported")
        self.assertEqual(result["summary"], "This claim is correct.")
    
    @patch('claims.utils.call_llm')
    def test_get_verdict_and_summary_fallback(self, mock_call_llm):
        """Test getting verdict with fallback response"""
        mock_call_llm.return_value = "FALLBACK_RESPONSE"
        
        result = get_verdict_and_summary("Test claim", "Evidence")
        
        self.assertEqual(result["verdict"], "not_found")
        self.assertIn("automatic fallback response", result["summary"])
    
    @patch('claims.utils.call_llm')
    def test_get_verdict_and_summary_max_retries(self, mock_call_llm):
        """Test getting verdict with maximum retries exceeded"""
        mock_call_llm.return_value = "Verdict: supported\nSummary: Contains \"invalid quote\" " \
        "not in evidence"
        
        evidence = "This is the evidence text."
        result = get_verdict_and_summary("Test claim", evidence)
        
        self.assertEqual(mock_call_llm.call_count, 4)  
        self.assertEqual(result["verdict"], "not_found")
        self.assertIn("Unable to generate a summary with accurate quotations", result["summary"])
    
    @patch('claims.utils.call_llm')
    def test_get_verdict_and_summary_error(self, mock_call_llm):
        """Test getting verdict with error"""
        mock_call_llm.side_effect = Exception("LLM error")
        
        result = get_verdict_and_summary("Test claim", "Evidence")
        
        self.assertEqual(result["verdict"], "not_found")
        self.assertIn("automatic fallback response", result["summary"])
    

    def test_verify_quotes_in_evidence_valid(self):
        """Test quote verification with valid quotes"""
        evidence = "The Earth is round and orbits the Sun."
        summary = "Evidence states that \"The Earth is round\" and it \"orbits the Sun\"."
        
        result = _verify_quotes_in_evidence(summary, evidence)
        
        self.assertTrue(result)
    
    def test_verify_quotes_in_evidence_invalid(self):
        """Test quote verification with invalid quotes"""
        evidence = "The Earth is round and orbits the Sun."
        summary = "Evidence states that \"The Earth is flat\" and it \"orbits around planets\"."
        
        result = _verify_quotes_in_evidence(summary, evidence)
        
        self.assertFalse(result)
    
    def test_verify_quotes_in_evidence_empty_quote(self):
        """Test quote verification with empty quotes"""
        evidence = "The Earth is round."
        summary = "Evidence states that \"\" is correct."
        
        result = _verify_quotes_in_evidence(summary, evidence)
        
        self.assertTrue(result)  
    
    def test_verify_quotes_in_evidence_no_quotes(self):
        """Test quote verification with no quotes"""
        evidence = "The Earth is round."
        summary = "Evidence supports this claim."
        
        result = _verify_quotes_in_evidence(summary, evidence)
        
        self.assertTrue(result) 
    
    @patch('claims.services.ClaimService.process_content_for_claims')
    def test_extract_claims_sync(self, mock_process):
        """Test synchronous claim extraction"""
        mock_process.return_value = ["Test claim"]
        with patch('claims.services.ClaimService') as mock_claim_service_class:
            mock_claim_service = MagicMock()
            mock_claim_service_class.return_value = mock_claim_service
            mock_claim_service.process_content_for_claims.return_value = ["Test claim"]
            
            result = extract_claims_sync("Test content", "post", 1)
            
            self.assertEqual(result, ["Test claim"])
            mock_claim_service.process_content_for_claims.assert_called_once()

    @patch('claims.utils.extract_claims_sync')
    def test_extract_claims_async(self, mock_extract_sync):
        """Test asynchronous claim extraction"""

        async def test_async():
            await extract_claims_async("Test content", "post", 1)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_async())
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        
        mock_extract_sync.assert_called_once_with("Test content", "post", 1)

    def test_create_content_prompt_without_context(self):
        """Test creating prompt without context"""
        content = "This is the content to analyze"
        
        prompt = _create_content_prompt(content)
        
        self.assertIn(content, prompt)
        self.assertIn("Extract all factual claims", prompt)
        self.assertNotIn("POST TITLE", prompt)

    def test_create_content_prompt_with_context(self):
        """Test creating prompt with context"""
        content = "This is the target comment"
        context = {
            "post": {
                "title": "Test Post",
                "content": "Test post content" 
            },
            "conversation_thread": [
                {"content": "Parent comment", "author": "user1", "depth": 0},
                {"content": "Reply to parent", "author": "user2", "depth": 1}
            ]
        }
        
        prompt = _create_content_prompt(content, context)
        
        self.assertIn("POST TITLE: Test Post", prompt)
        self.assertIn("POST CONTENT: Test post content", prompt)
        self.assertIn("CONVERSATION THREAD:", prompt)
        self.assertIn("Comment 1 by user1", prompt)
        self.assertIn("Comment 2 by user2", prompt)
        self.assertIn("TARGET COMMENT", prompt)
        self.assertIn(content, prompt)

    @patch('claims.utils.requests.post')
    def test_call_llm_error(self, mock_post):
        """Test LLM API call error handling - utils.py line 26-31"""
        mock_post.side_effect = Exception("API error")
        
        result = call_llm("Test prompt")
        
        self.assertEqual(result, "FALLBACK_RESPONSE")
    
    @patch('claims.utils.requests.post')
    def test_check_claim_with_wikipedia_error(self, mock_post):
        """Test Wikipedia API error handling - utils.py line 88-89, 98-100"""
        mock_post.side_effect = Exception("API error")
        
        result = check_claim_with_wikipedia("Test claim")
        
        self.assertIn("Unable to retrieve evidence", result["evidence"])
        self.assertEqual(result["sources"][0]["title"], "Error")
    
    def test_verify_quotes_in_evidence(self):
        """Test quote verification - utils.py line 118"""
        evidence = "The Earth is round and orbits the Sun."
        
        summary_valid = "Evidence states that \"The Earth is round\" which is correct."
        self.assertTrue(_verify_quotes_in_evidence(summary_valid, evidence))
        
        summary_invalid = "Evidence states that \"The Earth is flat\" which is incorrect."
        self.assertFalse(_verify_quotes_in_evidence(summary_invalid, evidence))
        
        summary_no_quotes = "Evidence supports the claim."
        self.assertTrue(_verify_quotes_in_evidence(summary_no_quotes, evidence))
    
    @patch('claims.utils.call_llm')
    def test_get_verdict_and_summary_with_invalid_quotes(self, mock_call_llm):
        """Test verdict generation with retries - utils.py line 139-153"""
        mock_call_llm.side_effect = [
            "Verdict: supported\nSummary: The evidence states that \"the earth is flat\" which"
            " is wrong.",
            "Verdict: supported\nSummary: The evidence states that the Earth is round."
        ]
        
        result = get_verdict_and_summary("The Earth is round", "The Earth is round and spherical.")
        
        self.assertEqual(mock_call_llm.call_count, 2)
        self.assertEqual(result["verdict"], "supported")
        
    @patch('claims.utils.call_llm')
    @patch('claims.utils.extract_claims_from_text')
    def test_extract_claims_with_context(self, mock_extract, mock_call_llm):
        """Test claim extraction with context - utils.py line 208, 225-233"""
        mock_extract.return_value = ["The Earth is round"]
        
        context = {
            "post": {
                "title": "Test Post",
                "content": "Post content"
            },
            "conversation_thread": [
                {"content": "Comment 1", "author": "user1"}
            ]
        }
        
        with patch('claims.utils._create_content_prompt') as mock_create_prompt:
            mock_create_prompt.return_value = "Test prompt with context"
            
            result = extract_claims_with_context("This is a test comment", context)
            
            mock_create_prompt.assert_called_once()
            mock_extract.assert_called_once_with("Test prompt with context")
            self.assertEqual(result, ["The Earth is round"])
    
 
    @patch('claims.utils.call_llm')
    def test_extract_claims_from_text_no_claims(self, mock_call_llm):
        """Test extraction with no claims - utils.py line 278, 284"""
        mock_call_llm.return_value = "(No factual claims found.)"
        
        result = extract_claims_from_text("This is an opinion.")
        
        self.assertEqual(result, [])
    
    @patch('claims.utils.call_llm')
    def test_extract_claims_from_text_with_error(self, mock_call_llm):
        """Test extraction with error - utils.py line 287-288"""
        mock_call_llm.side_effect = Exception("LLM error")
        
        result = extract_claims_from_text("Test content")
        
        self.assertEqual(result, ["Service temporarily unavailable."])
    
    
    @patch('claims.utils.call_llm')
    def test_get_verdict_and_summary_parse_error(self, mock_call_llm):
        """Test verdict parsing error - utils.py line 321-322"""
        mock_call_llm.return_value = "Invalid format without verdict or summary"
        
        result = get_verdict_and_summary("Test claim", "Test evidence")
        
        self.assertEqual(result["verdict"], "not_found")

        self.assertIsNotNone(result["summary"])

    @patch('claims.utils.call_llm')
    def test_get_verdict_and_summary_empty_response(self, mock_call_llm):
        """Test empty response - utils.py line 342-344"""
        mock_call_llm.return_value = ""
        
        result = get_verdict_and_summary("Test claim", "Test evidence")
        
        self.assertEqual(result["verdict"], "not_found")

        self.assertIsNotNone(result["summary"])
    
    @patch('claims.utils.requests.post')
    def test_check_claim_with_wikipedia_invalid_response(self, mock_post):
        """Test handling invalid Wikipedia response - utils.py line 370-409"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "response"}
        mock_post.return_value = mock_response
        
        result = check_claim_with_wikipedia("Test claim")
        
        self.assertIn("No relevant Wikipedia data", result["evidence"]) 

        self.assertTrue(isinstance(result["sources"], list))


class ClaimLinkedXmlTest(TestCase):
    """Tests for the XML claim linking functionality"""
    
    def setUp(self):
        self.sample_post_content = "The Amazon rainforest produces oxygen. " \
        "Climate change is concerning."
        self.sample_claims = [
            {
                "claim": {
                    "id": 1,
                    "extracted_claim": "The Amazon produces oxygen",
                }
            },
            {
                "claim": {
                    "id": 2,
                    "extracted_claim": "Climate change is concerning",
                }
            }
        ]

    def test_empty_claims_returns_wrapped_content(self):
        """Test that empty claims list returns the content wrapped in text tag"""
        result = generate_claim_linked_xml(self.sample_post_content, [])
        self.assertEqual(f"<text>{self.sample_post_content}</text>", result)
    
    @patch('claims.utils.call_llm')
    def test_xml_generation_preserves_original_text(self, mock_call_llm):
        """Test that XML generation preserves the original text exactly"""
        mock_call_llm.return_value = "1:The Amazon rainforest produces oxygen."
        
        result = generate_claim_linked_xml(self.sample_post_content, [self.sample_claims[0]])
        
        text_without_tags = re.sub(r'<[^>]+>', '', result)
        self.assertEqual(self.sample_post_content, text_without_tags)
    
    @patch('claims.utils.call_llm')
    def test_exact_claim_match(self, mock_call_llm):
        """Test claim matching when claim text appears exactly in content"""
        mock_call_llm.return_value = "NO_MATCH"
        
        content = "The Earth is round and rotates around the Sun."
        claims = [{
            "claim": {
                "id": 10,
                "extracted_claim": "The Earth is round",
            }
        }]
        
        result = generate_claim_linked_xml(content, claims)
        
        self.assertIn('<link id="10">The Earth is round</link>', result)
        self.assertIn('rotates around the Sun.', result)
    
    @patch('claims.utils.call_llm')
    def test_keyword_matching_fallback(self, mock_call_llm):
        """Test keyword matching when exact claim text isn't found"""
        mock_call_llm.return_value = "NO_MATCH" 
        
        content = "The Earth rotates on its axis. It also orbits the Sun."
        claims = [{
            "claim": {
                "id": 20,
                "extracted_claim": "Earth rotates daily",  
            }
        }]
        
        result = generate_claim_linked_xml(content, claims)
        
        self.assertIn('<link id="20">The Earth rotates on its axis</link>', result)
        self.assertIn('It also orbits the Sun.', result)
    
    @patch('claims.utils.call_llm')
    def test_no_matching_claim_segments(self, mock_call_llm):
        """Test when claim text has no match in content"""
        mock_call_llm.return_value = "NO_MATCH"  
        
        content = "The Sun is very hot."
        claims = [{
            "claim": {
                "id": 30,
                "extracted_claim": "Mercury is the closest planet to the Sun", 
            }
        }]
        
        result = generate_claim_linked_xml(content, claims)
        
        self.assertEqual("<text>The Sun is very hot.</text>", result)
    
    @patch('claims.utils.call_llm')
    def test_segment_no_overlap(self, mock_call_llm):
        """Test handling of non-overlapping segments"""
        mock_call_llm.return_value = "1:The Earth is round\n2:The Sun is hot"
        
        content = "The Earth is round. The Sun is hot."
        claims = [
            {"claim": {"id": 1, "extracted_claim": "Earth is round"}},
            {"claim": {"id": 2, "extracted_claim": "Sun is hot"}}
        ]
        
        result = generate_claim_linked_xml(content, claims)
        
        self.assertIn('<link id="1">The Earth is round</link>', result)
        self.assertIn('<link id="2">The Sun is hot</link>', result)
        self.assertEqual("<text><link id=\"1\">The Earth is round</link>. <link id=\"2\">The Sun"
        " is hot</link>.</text>", result)
    
    @patch('claims.utils.call_llm')
    def test_segment_large_overlap_keep_shorter(self, mock_call_llm):
        """Test handling of large segment overlap with shorter segment kept"""
        content = "Climate change is accelerating rapidly in recent years."
        claims = [
            {"claim": {"id": 1, "extracted_claim": "Climate change is accelerating rapidly"}},
            {"claim": {"id": 2, "extracted_claim": "Climate change is accelerating"}}
        ]
        
        mock_call_llm.return_value = "1:Climate change is accelerating rapidly\n2:Climate change" \
        " is accelerating"
        
        result = generate_claim_linked_xml(content, claims)
        
        self.assertNotIn('<link id="1">Climate change is accelerating rapidly</link>', result)
        self.assertIn('<link id="2">Climate change is accelerating</link>', result)
    
    @patch('claims.utils.call_llm')
    def test_segment_small_overlap_with_break_point(self, mock_call_llm):
        """Test handling of small segment overlap with natural break point"""
        content = "Climate change affects ecosystems worldwide"
        claims = [
            {"claim": {"id": 1, "extracted_claim": "Climate change affects"}},
            {"claim": {"id": 2, "extracted_claim": "affects ecosystems worldwide"}}
        ]
        
        mock_call_llm.return_value = "1:Climate change affects\n2:affects ecosystems worldwide"
        
        result = generate_claim_linked_xml(content, claims)
        
        self.assertIn('<link id="1">Climate change aff</link>', result)
        self.assertIn('<link id="2">ects ecosystems worldwide</link>', result)

    @patch('claims.utils.call_llm')
    def test_segment_small_overlap_midpoint_split(self, mock_call_llm):
        """Test handling of small segment overlap requiring midpoint split"""
        content = "Climatechangeaffectsecosystems"  
        
        mock_call_llm.return_value = "1:Climatechangeaffects\n2:affectsecosystems"
        
        claims = [
            {"claim": {"id": 1, "extracted_claim": "Climatechangeaffects"}},
            {"claim": {"id": 2, "extracted_claim": "affectsecosystems"}}
        ]
        
        result = generate_claim_linked_xml(content, claims)
        
        self.assertIn('<link id="1">Climatechangeaff</link>', result)
        self.assertIn('<link id="2">ectsecosystems</link>', result)
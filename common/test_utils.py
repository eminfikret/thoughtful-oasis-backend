from contextlib import contextmanager
from unittest import mock

from django.db.models.signals import post_save


@contextmanager
def disable_fact_checking_signals():
    """Temporarily disable post_save signals for fact checking during tests"""
    original_receivers = post_save.receivers
    original_sender_receivers = post_save.sender_receivers_cache.copy()

    post_save.receivers = []
    post_save.sender_receivers_cache.clear()
    
    try:
        yield
    finally:
        post_save.receivers = original_receivers
        post_save.sender_receivers_cache = original_sender_receivers


class MockLLMTestMixin:
    """Test mixin that patches LLM-related functions for all tests in a class"""
    
    def setUp(self):
        self.claims_patcher = mock.patch('claims.utils.extract_claims_from_text', 
                                         return_value=["Test claim"])
        self.mock_extract_claims = self.claims_patcher.start()
        
        self.call_llm_patcher = mock.patch('claims.utils.call_llm',
                                           return_value="Mocked LLM response")
        self.mock_call_llm = self.call_llm_patcher.start()
        
        super().setUp()
    
    def tearDown(self):

        self.claims_patcher.stop()
        self.call_llm_patcher.stop()
        super().tearDown()
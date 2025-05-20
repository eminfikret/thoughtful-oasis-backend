import asyncio
from unittest.mock import patch, MagicMock

from django.test import TestCase

from claims.models import Claim
from claims.services import ClaimService
from claims.utils import extract_claims_sync, extract_claims_async

class ClaimsUtilsTest(TestCase):
    """Tests for claims utility functions"""
    
    def setUp(self):
        # mock the claim service for testing
        self.mock_claim = MagicMock(spec=Claim)
        self.mock_claim.id = 1
        self.mock_claim.content_fragment = "Test claim"
        
        self.content = "This is a test content with claims"
        self.source_type = "post"
        self.source_id = 42
    
    @patch('claims.utils.claim_service')
    def test_extract_claims_sync(self, mock_service):
        """Test synchronous claim extraction"""
        mock_service.process_content_for_claims.return_value = [self.mock_claim]
        
        result = extract_claims_sync(self.content, self.source_type, self.source_id)

        mock_service.process_content_for_claims.assert_called_once_with(
            self.content, self.source_type, self.source_id
        )

        self.assertEqual(result, [self.mock_claim])
    
    @patch('claims.utils.claim_service')
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
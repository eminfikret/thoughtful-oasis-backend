from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Claim, FactCheck
import json

User = get_user_model()

class TextAnalysisControllerTest(TestCase):
    """Tests for TextAnalysisController"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.url = reverse('analyse-text')
    
    @patch('claims.controllers.ClaimService.process_raw_text')
    def test_analyse_text_success(self, mock_process):
        """Test successful text analysis"""
        mock_results = [
            {"claim": {"id": 1, "extracted_claim": "Test claim 1"},
             "fact_check": {"verdict": "supported", "summary": "Supported"}}
        ]
        mock_process.return_value = mock_results
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {"text": "Test content for analysis"},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['claims_count'], 1)
        self.assertEqual(response.data['results'], mock_results)
        mock_process.assert_called_once_with(self.user.id, "Test content for analysis")
    
    def test_analyse_text_invalid_data(self):
        """Test analysis with invalid data"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {"invalid_field": "Test content"},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('text', response.data)
    
    @patch('claims.controllers.ClaimService.process_raw_text')
    def test_analyse_text_server_error(self, mock_process):
        """Test server error during text analysis"""
        mock_process.side_effect = Exception("Processing error")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {"text": "Test content for analysis"},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class ClaimDetailControllerTest(TestCase):
    """Tests for ClaimDetailController"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Test claim",
            claim_index=1,
            source_type="raw"
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="supported",
            summary="Test summary"
        )
        
        self.url = reverse('claim-detail', kwargs={'claim_id': self.claim.id})
    
    @patch('claims.controllers.ClaimService.get_claim_with_fact_check')
    def test_get_claim_detail_success(self, mock_get_claim):
        """Test successful claim detail retrieval"""
        mock_result = {
            "claim": {"id": self.claim.id, "extracted_claim": "Test claim"},
            "fact_check": {"verdict": "supported", "summary": "Test summary"}
        }
        mock_get_claim.return_value = mock_result
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_result)
        mock_get_claim.assert_called_once_with(self.claim.id)
    
    @patch('claims.controllers.ClaimService.get_claim_with_fact_check')
    def test_get_claim_detail_not_found(self, mock_get_claim):
        """Test claim detail not found"""
        mock_get_claim.return_value = None
        
        self.client.force_authenticate(user=self.user)
        url = reverse('claim-detail', kwargs={'claim_id': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        
    @patch('claims.controllers.ClaimService.get_claim_with_fact_check')
    def test_get_claim_detail_server_error(self, mock_get_claim):
        """Test server error during claim detail retrieval"""
        mock_get_claim.side_effect = Exception("Database error")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class DeleteClaimControllerTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = 1
        self.claim_id = 123
        
    @patch('claims.controllers.ClaimService.delete_claim')
    def test_delete_claim_success(self, mock_delete):
        """Test successful claim deletion - controller.py line 146"""
 
        mock_delete.return_value = (True, "Claim deleted successfully")
    
        self.client.force_authenticate(user=MagicMock(id=self.user_id))
        url = reverse('delete-claim', kwargs={'claim_id': self.claim_id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_delete.assert_called_once_with(self.claim_id, self.user_id)
        
    @patch('claims.controllers.ClaimService.delete_claim')
    def test_delete_claim_forbidden(self, mock_delete):
        """Test permission denied claim deletion - controller.py lines 178-194"""

        mock_delete.return_value = (False, "You don't have permission to delete this claim")
        
        self.client.force_authenticate(user=MagicMock(id=self.user_id))
        url = reverse('delete-claim', kwargs={'claim_id': self.claim_id})
        response = self.client.delete(url)
   
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "You don't have permission to delete this claim")
        mock_delete.assert_called_once_with(self.claim_id, self.user_id)


class UserClaimsControllerTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = 1
        
    @patch('claims.controllers.ClaimService.get_user_claims')
    def test_get_user_claims_success(self, mock_get_claims):
        """Test getting user claims successfully - controller.py lines 228-240"""

        mock_claims = [
            {"claim": {"id": 1}, "fact_check": {"verdict": "supported"}},
            {"claim": {"id": 2}, "fact_check": {"verdict": "contradicted"}}
        ]
        mock_get_claims.return_value = mock_claims
        
        self.client.force_authenticate(user=MagicMock(id=self.user_id))
        url = reverse('user-claims')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['claims_count'], 2)
        self.assertEqual(response.data['claims'], mock_claims)
        mock_get_claims.assert_called_once_with(self.user_id)
        
    @patch('claims.controllers.ClaimService.get_user_claims')
    def test_get_user_claims_server_error(self, mock_get_claims):
        """Test server error when getting claims - controller.py lines 228-240"""

        mock_get_claims.side_effect = Exception("Database error")
        
        self.client.force_authenticate(user=MagicMock(id=self.user_id))
        url = reverse('user-claims')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
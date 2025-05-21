from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from ..models import Claim, FactCheck, FactCheckSource
from ..services import ClaimService
from unittest.mock import patch, MagicMock

User = get_user_model()

class ClaimControllersTest(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        self.refresh = RefreshToken.for_user(self.test_user)
        self.token = str(self.refresh.access_token)

        self.claim = Claim.objects.create(
            user_id=self.test_user.id,
            source_type='raw',
            extracted_claim='The Earth is round',
            claim_index=0
        )

        self.fact_check = FactCheck.objects.create(
            claim_id=self.claim.id,
            verdict='supported',
            summary='This claim is supported by scientific evidence.'
        )

        self.source = FactCheckSource.objects.create(
            fact_check_id=self.fact_check.id,
            url='https://en.wikipedia.org/wiki/Earth',
            title='Earth - Wikipedia',
            description='The Earth is the third planet from the Sun...',
            relevance_score=0.95
        )

    def authenticate(self):
        """Helper method to authenticate requests"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_text_analysis_successful(self):
        """Test submitting text for analysis"""
        self.authenticate()

        with patch.object(ClaimService, 'process_raw_text') as mock_process:

            mock_process.return_value = [
                {
                    "claim": {
                        "id": 1,
                        "extracted_claim": "The Earth is round",
                        "claim_index": 0
                    },
                    "fact_check": {
                        "id": 1,
                        "verdict": "supported",
                        "summary": "This claim is supported by scientific evidence.",
                        "sources": [
                            {
                                "id": 1,
                                "url": "https://en.wikipedia.org/wiki/Earth",
                                "title": "Earth - Wikipedia"
                            }
                        ]
                    }
                }
            ]
            
            url = reverse('analyse-text')
            data = {"text": "The Earth is round. This is a fact."}
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['message'], "Text analysed successfully")
            self.assertEqual(response.data['claims_count'], 1)
            self.assertEqual(len(response.data['results']), 1)

            mock_process.assert_called_once_with(self.test_user.id, "The Earth is round. This is a fact.")

    def test_text_analysis_invalid_data(self):
        """Test submitting invalid data for analysis"""
        self.authenticate()
        
        url = reverse('analyse-text')
        data = {}  
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('text', response.data)

    def test_text_analysis_unauthorized(self):
        """Test attempting to submit text without authentication"""

        url = reverse('analyse-text')
        data = {"text": "The Earth is round."}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_claim_detail_successful(self):
        """Test retrieving details for an existing claim"""
        self.authenticate()

        with patch.object(ClaimService, 'get_claim_with_fact_check') as mock_get:
            mock_get.return_value = {
                "claim": {
                    "id": self.claim.id,
                    "extracted_claim": "The Earth is round",
                    "source_type": "raw",
                    "claim_index": 0,
                    "created_at": self.claim.created_at.isoformat()
                },
                "fact_check": {
                    "id": self.fact_check.id,
                    "verdict": "supported",
                    "summary": "This claim is supported by scientific evidence.",
                    "sources": [
                        {
                            "id": self.source.id,
                            "url": "https://en.wikipedia.org/wiki/Earth",
                            "title": "Earth - Wikipedia",
                            "description": "The Earth is the third planet from the Sun..."
                        }
                    ]
                }
            }
            
            url = reverse('claim-detail', args=[self.claim.id])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['claim']['id'], self.claim.id)
            self.assertEqual(response.data['claim']['extracted_claim'], "The Earth is round")
            self.assertEqual(response.data['fact_check']['verdict'], "supported")

    def test_claim_detail_not_found(self):
        """Test retrieving details for a non-existent claim"""
        self.authenticate()

        with patch.object(ClaimService, 'get_claim_with_fact_check') as mock_get:
            mock_get.return_value = None
            
            url = reverse('claim-detail', args=[9999]) 
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertIn('error', response.data)

    def test_claim_detail_unauthorized(self):
        """Test attempting to retrieve claim details without authentication"""

        url = reverse('claim-detail', args=[self.claim.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_claim_detail_database_error(self):
        """Test handling database schema mismatch errors"""
        self.authenticate()

        with patch.object(ClaimService, 'get_claim_with_fact_check') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            url = reverse('claim-detail', args=[self.claim.id])
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)

    def test_text_analysis_server_error(self):
        """Test handling server errors during text analysis"""
        self.authenticate()

        with patch.object(ClaimService, 'process_raw_text') as mock_process:
            mock_process.side_effect = Exception("Processing error")
            
            url = reverse('analyse-text')
            data = {"text": "The Earth is round."}
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
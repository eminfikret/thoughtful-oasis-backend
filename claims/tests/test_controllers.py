from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from claims.models import Claim, FactCheck, FactCheckSource


class ClaimControllerTest(APITestCase):
    """Tests for ClaimController"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('submit-claim')
        
        self.perm_patcher = patch('claims.controllers.ClaimController.permission_classes', [])
        self.auth_patcher = patch('claims.controllers.ClaimController.authentication_classes', [])
        self.perm_patcher.start()
        self.auth_patcher.start()
    
    def tearDown(self):
        self.perm_patcher.stop()
        self.auth_patcher.stop()
    
    def test_post_valid_claim(self):
        """Test submitting a valid claim"""
        data = {
            'content': "The Earth is flat",
            'content_position': {"start": 0, "end": 16}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('claim', response.data)
        self.assertIn('id', response.data['claim'])
        self.assertEqual(response.data['claim']['content_fragment'], "The Earth is flat")

        claim_id = response.data['claim']['id']
        claim = Claim.objects.get(id=claim_id)
        self.assertEqual(claim.content_fragment, "The Earth is flat")
        self.assertIsNone(claim.post_id)
        self.assertIsNone(claim.comment_id)
        self.assertEqual(claim.content_position, {"start": 0, "end": 16})
    
    def test_post_claim_without_content_position(self):
        """Test submitting a claim without content position"""
        data = {
            'content': "The Earth is flat"
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('claim', response.data)
        
        claim_id = response.data['claim']['id']
        claim = Claim.objects.get(id=claim_id)
        self.assertEqual(claim.content_position, {"start": 0, "end": len(data['content'])})
    
    def test_post_invalid_claim(self):
        """Test submitting an invalid claim"""
        data = {
            'content_position': {"start": 0, "end": 16}
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)


class ClaimDetailControllerTest(APITestCase):
    """Tests for ClaimDetailController"""
    
    def setUp(self):
        self.client = APIClient()

        self.claim = Claim.objects.create(
            content_fragment="The Earth is flat",
            content_position={"start": 0, "end": 16}
        )

        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="contradicted",
            summary="The Earth is an oblate spheroid"
        )

        self.source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://nasa.gov/earth",
            title="NASA Earth Facts"
        )

        self.url = reverse('claim-detail', args=[self.claim.id])
        self.nonexistent_url = reverse('claim-detail', args=[99999])

        self.perm_patcher = patch('claims.controllers.ClaimDetailController.permission_classes', [])
        self.auth_patcher = patch('claims.controllers.ClaimDetailController.authentication_classes',
                                   [])
        self.perm_patcher.start()
        self.auth_patcher.start()
    
    def tearDown(self):
        self.perm_patcher.stop()
        self.auth_patcher.stop()
    
    def test_get_existing_claim(self):
        """Test getting details for an existing claim"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.claim.id)
        self.assertEqual(response.data['content_fragment'], "The Earth is flat")
        self.assertEqual(response.data['content_position'], {"start": 0, "end": 16})
        self.assertIn('created_at', response.data)
    
    def test_get_nonexistent_claim(self):
        """Test getting details for a non-existent claim"""
        response = self.client.get(self.nonexistent_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "Claim not found")
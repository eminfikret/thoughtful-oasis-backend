from django.test import TestCase

from claims.models import Claim, FactCheck, FactCheckSource


class ClaimModelTest(TestCase):
    """Tests for the Claim model"""
    
    def setUp(self):
        self.standalone_claim = Claim.objects.create(
            content_fragment="The Earth is flat",
            content_position={"start": 0, "end": 16}
        )
        
        self.post_claim = Claim.objects.create(
            post_id=1,
            content_fragment="Water is a liquid",
            content_position={"start": 5, "end": 39}
        )
        
        self.comment_claim = Claim.objects.create(
            comment_id=2,
            content_fragment="Venus is a planet",
            content_position={"start": 10, "end": 30}
        )
    
    def test_claim_creation(self):
        """Test that claims can be created with different source types"""
        self.assertIsNone(self.standalone_claim.post_id)
        self.assertIsNone(self.standalone_claim.comment_id)
        self.assertEqual(self.standalone_claim.content_fragment, "The Earth is flat")
        
        self.assertEqual(self.post_claim.post_id, 1)
        self.assertIsNone(self.post_claim.comment_id)
        
        self.assertEqual(self.comment_claim.comment_id, 2)
        self.assertIsNone(self.comment_claim.post_id)
    
    def test_string_representation(self):
        """Test the string representation of claims"""
        self.assertTrue("Standalone claim" in str(self.standalone_claim))
        self.assertTrue("Post #1" in str(self.post_claim))
        self.assertTrue("Comment #2" in str(self.comment_claim))


class FactCheckModelTest(TestCase):
    """Tests for the FactCheck model"""
    
    def setUp(self):
        self.claim = Claim.objects.create(
            content_fragment="The Earth is flat",
            content_position={"start": 0, "end": 16}
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="contradicted",
            summary="The Earth is actually a sphere"
        )
    
    def test_fact_check_creation(self):
        """Test fact check creation"""
        self.assertEqual(self.fact_check.claim, self.claim)
        self.assertEqual(self.fact_check.verdict, "contradicted")
        self.assertEqual(self.fact_check.summary, "The Earth is actually a sphere")
    
    def test_string_representation(self):
        """Test the string representation of fact checks"""
        self.assertTrue(f"Fact check for claim #{self.claim.id}" in str(self.fact_check))
        self.assertTrue("contradicted" in str(self.fact_check))


class FactCheckSourceModelTest(TestCase):
    """Tests for the FactCheckSource model"""
    
    def setUp(self):
        self.claim = Claim.objects.create(
            content_fragment="The Earth is flat",
            content_position={"start": 0, "end": 16}
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="contradicted",
            summary="The Earth is actually a sphere"
        )
        
        self.source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://wikipedia.org/wiki/Earth",
            title="NASA Earth Facts",
            description="Official NASA page about Earth",
            relevance_score=0.95
        )
    
    def test_source_creation(self):
        """Test fact check source creation"""
        self.assertEqual(self.source.fact_check, self.fact_check)
        self.assertEqual(self.source.url, "https://wikipedia.org/wiki/Earth")
        self.assertEqual(self.source.title, "NASA Earth Facts")
        self.assertEqual(self.source.relevance_score, 0.95)
    
    def test_string_representation(self):
        """Test the string representation of fact check sources"""
        self.assertTrue(f"Source for fact check #{self.fact_check.id}" in str(self.source))
        self.assertTrue("NASA Earth Facts" in str(self.source))
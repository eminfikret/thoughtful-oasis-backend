from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from claims.models import Claim, FactCheck, FactCheckSource

User = get_user_model()


class ClaimModelTest(TestCase):
    """Tests for the Claim model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        self.standalone_claim = Claim.objects.create(
            extracted_claim="The Earth is flat",
            claim_index=1,
            source_type="raw",
            source_text="The Earth is flat and sits on the back of a turtle."
        )
        
        self.post_claim = Claim.objects.create(
            post_id=1,
            extracted_claim="Water is a liquid",
            claim_index=1,
            source_type="post"
        )
        
        self.comment_claim = Claim.objects.create(
            comment_id=2,
            extracted_claim="Venus is a planet",
            claim_index=2,
            source_type="comment"
        )
        
        self.user_claim = Claim.objects.create(
            user=self.user,
            extracted_claim="The moon orbits Earth",
            claim_index=1,
            source_type="raw",
            source_text="The moon orbits Earth at a distance of 384,400 km."
        )
    
    def test_claim_creation(self):
        """Test that claims can be created with different source types"""
        self.assertIsNone(self.standalone_claim.post_id)
        self.assertIsNone(self.standalone_claim.comment_id)
        self.assertEqual(self.standalone_claim.extracted_claim, "The Earth is flat")
        self.assertEqual(self.standalone_claim.source_type, "raw")
        self.assertEqual(self.standalone_claim.source_text, 
                         "The Earth is flat and sits on the back of a turtle.")
        
        self.assertEqual(self.post_claim.post_id, 1)
        self.assertIsNone(self.post_claim.comment_id)
        self.assertEqual(self.post_claim.source_type, "post")
        
        self.assertEqual(self.comment_claim.comment_id, 2)
        self.assertIsNone(self.comment_claim.post_id)
        self.assertEqual(self.comment_claim.source_type, "comment")
        
        self.assertEqual(self.user_claim.user, self.user)
        
    def test_string_representation(self):
        """Test the string representation of claims"""
        self.assertIn("Raw text:", str(self.standalone_claim))
        self.assertIn("The Earth is flat", str(self.standalone_claim))
        
        self.assertIn("Post #1:", str(self.post_claim))
        self.assertIn("Water is a liquid", str(self.post_claim))
        
        self.assertIn("Comment #2:", str(self.comment_claim))
        self.assertIn("Venus is a planet", str(self.comment_claim))
        
    def test_claim_required_fields(self):
        """Test that required fields must be provided"""
        with self.assertRaises(IntegrityError):
            Claim.objects.create(
                source_type="raw"
            )
            
    def test_source_type_validation(self):
        """Test that source_type must be one of the valid choices"""
        with self.assertRaises(ValidationError):
            claim = Claim(
                extracted_claim="Invalid source type",
                claim_index=1,
                source_type="invalid_type" 
            )
            claim.full_clean() 
            
    def test_user_deletion_cascade(self):
        """Test that deleting a user also deletes their claims"""
        user_id = self.user.id
        self.user.delete()
        
        with self.assertRaises(Claim.DoesNotExist):
            Claim.objects.get(user_id=user_id)


class FactCheckModelTest(TestCase):
    """Tests for the FactCheck model"""
    
    def setUp(self):
        self.claim = Claim.objects.create(
            extracted_claim="The Earth is flat",
            claim_index=1,
            source_type="raw"
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
    
    def test_verdict_choices(self):
        """Test that verdict must be one of the valid choices"""
        with self.assertRaises(ValidationError):
            fact_check = FactCheck(
                claim=self.claim,
                verdict="invalid_verdict", 
                summary="This should fail"
            )
            fact_check.full_clean() 
            
    def test_claim_deletion_cascade(self):
        """Test that deleting a claim also deletes its fact check"""
        claim_id = self.claim.id
        self.claim.delete()
        

        with self.assertRaises(FactCheck.DoesNotExist):
            FactCheck.objects.get(claim_id=claim_id)
            
    def test_one_to_one_constraint(self):
        """Test that only one fact check can exist per claim"""
        with self.assertRaises(IntegrityError):

            FactCheck.objects.create(
                claim=self.claim,
                verdict="supported",
                summary="This should fail due to one-to-one constraint"
            )


class FactCheckSourceModelTest(TestCase):
    """Tests for the FactCheckSource model"""
    
    def setUp(self):
        self.claim = Claim.objects.create(
            extracted_claim="The Earth is flat",
            claim_index=1,
            source_type="raw"
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
        """Test source creation"""
        self.assertEqual(self.source.fact_check, self.fact_check)
        self.assertEqual(self.source.url, "https://wikipedia.org/wiki/Earth")
        self.assertEqual(self.source.title, "NASA Earth Facts")
        self.assertEqual(self.source.description, "Official NASA page about Earth")
        self.assertEqual(self.source.relevance_score, 0.95)
    
    def test_string_representation(self):
        """Test the string representation of sources"""
        self.assertTrue(f"Source for fact check #{self.fact_check.id}" in str(self.source))
        self.assertTrue("NASA Earth Facts" in str(self.source))
        
    def test_fact_check_deletion_cascade(self):
        """Test that deleting a fact check also deletes its sources"""
        fact_check_id = self.fact_check.id
        self.fact_check.delete()
        
        with self.assertRaises(FactCheckSource.DoesNotExist):
            FactCheckSource.objects.get(fact_check_id=fact_check_id)
            
    def test_multiple_sources_per_fact_check(self):
        """Test that multiple sources can be added to a fact check"""
        second_source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://example.com/earth-science",
            title="Earth Science",
            description="Scientific data about Earth",
            relevance_score=0.85
        )
        
        sources = FactCheckSource.objects.filter(fact_check=self.fact_check)
        self.assertEqual(sources.count(), 2)
        self.assertIn(self.source, sources)
        self.assertIn(second_source, sources)
        
    def test_blank_fields(self):
        """Test that optional fields can be blank"""
        source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://example.com/minimal",
            title="Minimal Source",

        )
        
        self.assertIsNone(source.description)
        self.assertIsNone(source.relevance_score)
        
    def test_url_validation(self):
        """Test that URL validation works"""
        with self.assertRaises(ValidationError):
            source = FactCheckSource(
                fact_check=self.fact_check,
                url="not-a-valid-url",  
                title="Invalid URL Test"
            )
            source.full_clean()
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import IntegrityError

from claims.models import Claim, FactCheck, FactCheckSource
from claims.repositories import ClaimRepository, FactCheckRepository

User = get_user_model()


class ClaimRepositoryTest(TestCase):
    """Tests for the ClaimRepository"""
    
    def setUp(self):
        self.claim_repo = ClaimRepository()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        self.user_claim = Claim.objects.create(
            user=self.user,
            extracted_claim="User's claim",
            claim_index=1,
            source_type="raw",
            source_text="Original text"
        )
        
        self.post_claim = Claim.objects.create(
            post_id=42,
            extracted_claim="Post claim",
            claim_index=1,
            source_type="post"
        )
        
        self.comment_claim = Claim.objects.create(
            comment_id=24,
            extracted_claim="Comment claim",
            claim_index=1,
            source_type="comment"
        )

        self.claim_data = {
            'user_id': self.user.id,
            'extracted_claim': "New test claim",
            'claim_index': 2,
            'source_type': "raw",
            'source_text': "Test source text"
        }
    
    def test_create_claim(self):
        """Test creating a claim through the repository"""
        claim = self.claim_repo.create_claim(**self.claim_data)
        
        self.assertEqual(claim.user_id, self.user.id)
        self.assertEqual(claim.extracted_claim, "New test claim")
        self.assertEqual(claim.claim_index, 2)
        self.assertEqual(claim.source_type, "raw")
        self.assertEqual(claim.source_text, "Test source text")

        saved_claim = Claim.objects.get(id=claim.id)
        self.assertEqual(saved_claim.extracted_claim, "New test claim")
    
    def test_create_claim_post_source(self):
        """Test creating a claim with post source"""
        claim = self.claim_repo.create_claim(
            user_id=self.user.id,
            extracted_claim="Post source claim",
            claim_index=3,
            source_type="post",
            post_id=99
        )
        
        self.assertEqual(claim.post_id, 99)
        self.assertEqual(claim.source_type, "post")
        self.assertIsNone(claim.source_text)
        self.assertIsNone(claim.comment_id)
    
    def test_create_claim_comment_source(self):
        """Test creating a claim with comment source"""
        claim = self.claim_repo.create_claim(
            user_id=self.user.id,
            extracted_claim="Comment source claim",
            claim_index=4,
            source_type="comment",
            comment_id=88
        )
        
        self.assertEqual(claim.comment_id, 88)
        self.assertEqual(claim.source_type, "comment")
        self.assertIsNone(claim.source_text)
        self.assertIsNone(claim.post_id)
    
    def test_get_claim_by_id(self):
        """Test retrieving a claim by ID"""
        claim = self.claim_repo.get_claim_by_id(self.user_claim.id)
        self.assertEqual(claim.id, self.user_claim.id)
        self.assertEqual(claim.extracted_claim, "User's claim")

        non_existent_claim = self.claim_repo.get_claim_by_id(99999)
        self.assertIsNone(non_existent_claim)
    
    def test_get_claims_for_user(self):
        """Test getting claims for a specific user"""
        claims = self.claim_repo.get_claims_for_user(self.user.id)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].extracted_claim, "User's claim")

        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        other_claims = self.claim_repo.get_claims_for_user(other_user.id)
        self.assertEqual(len(other_claims), 0)
    
    def test_get_claims_for_post(self):
        """Test getting claims for a specific post"""
        claims = self.claim_repo.get_claims_for_post(42)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].extracted_claim, "Post claim")

        no_claims = self.claim_repo.get_claims_for_post(999)
        self.assertEqual(len(no_claims), 0)
    
    def test_get_claims_for_comment(self):
        """Test getting claims for a specific comment"""
        claims = self.claim_repo.get_claims_for_comment(24)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].extracted_claim, "Comment claim")

        no_claims = self.claim_repo.get_claims_for_comment(999)
        self.assertEqual(len(no_claims), 0)
    
    def test_search_claims(self):
        """Test searching claims by text"""
        claims = self.claim_repo.search_claims("User")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].id, self.user_claim.id)

        claims = self.claim_repo.search_claims("Original")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].id, self.user_claim.id)

        claims = self.claim_repo.search_claims("nonexistent")
        self.assertEqual(len(claims), 0)
    
    def test_search_claims_case_insensitive(self):
        """Test that search is case-insensitive"""
        claims = self.claim_repo.search_claims("user")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].id, self.user_claim.id)
        
        claims = self.claim_repo.search_claims("ORIGINAL")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].id, self.user_claim.id)
        
    def test_search_claims_partial_match(self):
        """Test that search works with partial matches"""
        claims = self.claim_repo.search_claims("claim")
        self.assertEqual(len(claims), 3) 
    
    def test_bulk_create_claims(self):
        """Test bulk creation of claims"""
        claims_data = [
            {
                'user_id': self.user.id,
                'extracted_claim': "Bulk claim 1",
                'claim_index': 5,
                'source_type': "raw"
            },
            {
                'user_id': self.user.id,
                'extracted_claim': "Bulk claim 2",
                'claim_index': 6,
                'source_type': "raw"
            }
        ]
        
        claims = self.claim_repo.bulk_create_claims(claims_data)
        
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0].extracted_claim, "Bulk claim 1")
        self.assertEqual(claims[1].extracted_claim, "Bulk claim 2")

        db_claims = Claim.objects.filter(extracted_claim__startswith="Bulk")
        self.assertEqual(len(db_claims), 2)
    
    def test_update_claim(self):
        """Test updating a claim"""
        updated = self.claim_repo.update_claim(
            self.user_claim.id, 
            extracted_claim="Updated claim text"
        )
        
        self.assertTrue(updated)
        
        refreshed_claim = Claim.objects.get(id=self.user_claim.id)
        self.assertEqual(refreshed_claim.extracted_claim, "Updated claim text")
    
    def test_update_nonexistent_claim(self):
        """Test updating a non-existent claim"""
        updated = self.claim_repo.update_claim(
            99999,  
            extracted_claim="This won't work"
        )
        
        self.assertFalse(updated)
    
    def test_delete_claim(self):
        """Test deleting a claim"""
        claim_id = self.user_claim.id
        deleted = self.claim_repo.delete_claim(claim_id)
        
        self.assertTrue(deleted)
        
        with self.assertRaises(Claim.DoesNotExist):
            Claim.objects.get(id=claim_id)
    
    def test_delete_nonexistent_claim(self):
        """Test deleting a non-existent claim"""
        deleted = self.claim_repo.delete_claim(99999) 
        
        self.assertFalse(deleted)


class FactCheckRepositoryTest(TestCase):
    """Tests for the FactCheckRepository"""
    
    def setUp(self):
        self.fact_check_repo = FactCheckRepository()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Test claim for fact checking",
            claim_index=1,
            source_type="raw"
        )
        
        self.another_claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Another test claim",
            claim_index=2,
            source_type="raw"
        )
    
    def test_create_fact_check(self):
        """Test creating a fact check"""
        fact_check = self.fact_check_repo.create_fact_check(
            claim_id=self.claim.id,
            verdict="supported",
            summary="Test summary"
        )
        
        self.assertEqual(fact_check.claim_id, self.claim.id)
        self.assertEqual(fact_check.verdict, "supported")
        self.assertEqual(fact_check.summary, "Test summary")
        
        db_fact_check = FactCheck.objects.get(id=fact_check.id)
        self.assertEqual(db_fact_check.verdict, "supported")
    
    def test_create_fact_check_source(self):
        """Test creating a fact check source"""
        fact_check = self.fact_check_repo.create_fact_check(
            claim_id=self.claim.id,
            verdict="supported",
            summary="Test summary"
        )
        
        source = self.fact_check_repo.create_fact_check_source(
            fact_check_id=fact_check.id,
            url="https://example.com/test",
            title="Test Source",
            description="Test description",
            relevance_score=0.8
        )
        
        self.assertEqual(source.fact_check_id, fact_check.id)
        self.assertEqual(source.url, "https://example.com/test")
        self.assertEqual(source.title, "Test Source")
        self.assertEqual(source.description, "Test description")
        self.assertEqual(source.relevance_score, 0.8)

        db_source = FactCheckSource.objects.get(id=source.id)
        self.assertEqual(db_source.title, "Test Source")
    
    def test_create_fact_check_with_sources(self):
        """Test creating a fact check with sources in one transaction"""
        fact_check_data = {
            'claim_id': self.claim.id,
            'verdict': 'contradicted',
            'summary': 'Test summary with sources'
        }
        
        sources_data = [
            {
                'url': 'https://example.com/source1',
                'title': 'Source 1',
                'description': 'First test source'
            },
            {
                'url': 'https://example.com/source2',
                'title': 'Source 2',
                'description': 'Second test source',
                'relevance_score': 0.9
            }
        ]
        
        fact_check = self.fact_check_repo.create_fact_check_with_sources(
            fact_check_data, sources_data
        )
        
        self.assertEqual(fact_check.claim_id, self.claim.id)
        self.assertEqual(fact_check.verdict, 'contradicted')

        sources = FactCheckSource.objects.filter(fact_check=fact_check)
        self.assertEqual(sources.count(), 2)
        self.assertEqual(sources[0].title, 'Source 1')
        self.assertEqual(sources[1].title, 'Source 2')
    
    def test_get_fact_check_by_id(self):
        """Test retrieving a fact check by ID"""
        fact_check = self.fact_check_repo.create_fact_check(
            claim_id=self.claim.id,
            verdict="supported",
            summary="Test summary"
        )
        
        retrieved = self.fact_check_repo.get_fact_check_by_id(fact_check.id)
        self.assertEqual(retrieved.id, fact_check.id)
        self.assertEqual(retrieved.verdict, "supported")
        
        non_existent = self.fact_check_repo.get_fact_check_by_id(99999)
        self.assertIsNone(non_existent)
    
    def test_get_fact_check_by_claim_id(self):
        """Test retrieving a fact check by claim ID"""
        fact_check = self.fact_check_repo.create_fact_check(
            claim_id=self.claim.id,
            verdict="supported",
            summary="Test summary"
        )
        
        retrieved = self.fact_check_repo.get_fact_check_by_claim_id(self.claim.id)
        self.assertEqual(retrieved.id, fact_check.id)
        self.assertEqual(retrieved.verdict, "supported")

        non_existent = self.fact_check_repo.get_fact_check_by_claim_id(99999)
        self.assertIsNone(non_existent)
    
    def test_get_fact_checks_for_claim(self):
        """Test getting fact checks for a specific claim"""
        self.fact_check_repo.create_fact_check(
            claim_id=self.claim.id,
            verdict="supported",
            summary="Test summary"
        )
        
        fact_checks = self.fact_check_repo.get_fact_checks_for_claim(self.claim.id)
        self.assertEqual(len(fact_checks), 1)
        self.assertEqual(fact_checks[0].verdict, "supported")

        no_checks = self.fact_check_repo.get_fact_checks_for_claim(self.another_claim.id)
        self.assertEqual(len(no_checks), 0)
    
    def test_update_fact_check(self):
        """Test updating a fact check"""
        fact_check = self.fact_check_repo.create_fact_check(
            claim_id=self.claim.id,
            verdict="supported",
            summary="Original summary"
        )
        
        updated = self.fact_check_repo.update_fact_check(
            fact_check.id,
            verdict="contradicted",
            summary="Updated summary"
        )
        
        self.assertTrue(updated)
        
        refreshed = FactCheck.objects.get(id=fact_check.id)
        self.assertEqual(refreshed.verdict, "contradicted")
        self.assertEqual(refreshed.summary, "Updated summary")
    
    def test_update_nonexistent_fact_check(self):
        """Test updating a non-existent fact check"""
        updated = self.fact_check_repo.update_fact_check(
            99999,  
            verdict="not_found",
            summary="This won't work"
        )
        
        self.assertFalse(updated)
    
    def test_delete_fact_check(self):
        """Test deleting a fact check"""
        fact_check = self.fact_check_repo.create_fact_check(
            claim_id=self.claim.id,
            verdict="supported",
            summary="Test summary"
        )
        
        fact_check_id = fact_check.id
        deleted = self.fact_check_repo.delete_fact_check(fact_check_id)
        
        self.assertTrue(deleted)
        
        with self.assertRaises(FactCheck.DoesNotExist):
            FactCheck.objects.get(id=fact_check_id)
    
    def test_delete_nonexistent_fact_check(self):
        """Test deleting a non-existent fact check"""
        deleted = self.fact_check_repo.delete_fact_check(99999)
        
        self.assertFalse(deleted)
    
    def test_transaction_rollback(self):
        """Test that transactions are rolled back on error"""
        claim = Claim.objects.create(
            extracted_claim="Test claim for transaction",
            claim_index=1,
            source_type="raw"
        )

        fact_check_id = self.fact_check_repo.create_fact_check(
            claim_id=claim.id,
            verdict="supported",
            summary="This is a valid fact check"
        ).id

        with self.assertRaises(IntegrityError):
            self.fact_check_repo.create_fact_check(
                claim_id=claim.id,
                verdict="contradicted",
                summary="This should fail due to one-to-one constraint"
            )

        fact_checks = FactCheck.objects.filter(claim_id=claim.id)
        self.assertEqual(len(fact_checks), 1)
        self.assertEqual(fact_checks[0].id, fact_check_id)
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase

from ..models import Claim, FactCheckSource
from ..repositories import ClaimRepository, FactCheckRepository

User = get_user_model()


class ClaimRepositoryTest(TestCase):
    """Tests for the ClaimRepository class"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='23123###444gdfggg'
        )
        
        self.claim_repository = ClaimRepository()

        self.raw_claim = self.claim_repository.create_claim(
            user_id=self.user.id,
            extracted_claim="The Earth is round",
            claim_index=1,
            source_type="raw",
            source_text="The Earth is round and this is a scientific fact."
        )
        
        self.post_claim = self.claim_repository.create_claim(
            user_id=self.user.id,
            extracted_claim="Water freezes at 0°C",
            claim_index=2,
            source_type="post",
            post_id=123
        )
        
        self.comment_claim = self.claim_repository.create_claim(
            user_id=self.user.id,
            extracted_claim="Humans need oxygen",
            claim_index=3,
            source_type="comment",
            comment_id=456
        )

    def test_create_claim(self):
        """Test creating a claim"""
        claim = self.claim_repository.create_claim(
            user_id=self.user.id,
            extracted_claim="New test claim",
            claim_index=4,
            source_type="raw",
            source_text="New test claim text"
        )
        
        self.assertIsNotNone(claim.id)
        self.assertEqual(claim.extracted_claim, "New test claim")
        self.assertEqual(claim.claim_index, 4)
        self.assertEqual(claim.source_type, "raw")
        self.assertEqual(claim.source_text, "New test claim text")
        self.assertEqual(claim.user_id, self.user.id)

    def test_get_claim_by_id_existing(self):
        """Test getting an existing claim by ID"""
        claim = self.claim_repository.get_claim_by_id(self.raw_claim.id)
        
        self.assertEqual(claim, self.raw_claim)
        self.assertEqual(claim.extracted_claim, "The Earth is round")

    def test_get_claim_by_id_non_existing(self):
        """Test getting a non-existing claim by ID"""
        claim = self.claim_repository.get_claim_by_id(999999)
        
        self.assertIsNone(claim)

    def test_get_claims_for_user(self):
        """Test getting claims for a user"""
        claims = self.claim_repository.get_claims_for_user(self.user.id)
        
        self.assertEqual(len(claims), 3)
        self.assertIn(self.raw_claim, claims)
        self.assertIn(self.post_claim, claims)
        self.assertIn(self.comment_claim, claims)

    def test_get_claims_for_user_non_existing(self):
        """Test getting claims for non-existing user"""
        claims = self.claim_repository.get_claims_for_user(999999)
        
        self.assertEqual(len(claims), 0)

    def test_delete_claim(self):
        """Test deleting a claim"""
        claim_id = self.raw_claim.id
        
        self.claim_repository.delete_claim(claim_id)
        
        self.assertIsNone(self.claim_repository.get_claim_by_id(claim_id))


class FactCheckRepositoryTest(TestCase):
    """Tests for the FactCheckRepository class"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='23123###444gdfggg'
        )

        self.fact_check_repository = FactCheckRepository()
        self.claim_repository = ClaimRepository()

        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="The Earth is round",
            claim_index=1,
            source_type="raw",
            source_text="The Earth is round and this is a scientific fact."
        )

        self.fact_check = self.fact_check_repository.create_fact_check(
            claim_id=self.claim.id,
            verdict="supported",
            summary="This claim is supported by scientific evidence"
        )

        self.source1 = self.fact_check_repository.create_fact_check_source(
            fact_check_id=self.fact_check.id,
            url="https://en.wikipedia.org/wiki/Earth",
            title="Earth - Wikipedia",
            description="The Earth is the third planet from the Sun...",
            relevance_score=0.95
        )
        
        self.source2 = self.fact_check_repository.create_fact_check_source(
            fact_check_id=self.fact_check.id,
            url="https://nasa.gov/earth",
            title="NASA Earth Facts",
            description="NASA's official Earth information page",
            relevance_score=0.90
        )

        self.claim_without_check = Claim.objects.create(
            user=self.user,
            extracted_claim="Unverified claim",
            claim_index=2,
            source_type="raw",
            source_text="This claim has no fact check yet"
        )

    def test_create_fact_check(self):
        """Test creating a fact check"""
        fact_check = self.fact_check_repository.create_fact_check(
            claim_id=self.claim_without_check.id,
            verdict="contradicted",
            summary="This claim is contradicted by evidence"
        )
        
        self.assertIsNotNone(fact_check.id)
        self.assertEqual(fact_check.claim_id, self.claim_without_check.id)
        self.assertEqual(fact_check.verdict, "contradicted")
        self.assertEqual(fact_check.summary, "This claim is contradicted by evidence")

    def test_create_fact_check_duplicate(self):
        """Test creating a duplicate fact check for the same claim (should fail)"""
        with self.assertRaises(IntegrityError):
            self.fact_check_repository.create_fact_check(
                claim_id=self.claim.id,
                verdict="not_found",
                summary="This is a duplicate fact check"
            )

    def test_get_fact_check_by_claim_id_existing(self):
        """Test getting a fact check by claim ID when it exists"""
        fact_check = self.fact_check_repository.get_fact_check_by_claim_id(self.claim.id)
        
        self.assertEqual(fact_check, self.fact_check)
        self.assertEqual(fact_check.verdict, "supported")
        self.assertEqual(fact_check.summary, "This claim is supported by scientific evidence")

    def test_get_fact_check_by_claim_id_non_existing(self):
        """Test getting a fact check by claim ID when it doesn't exist"""
        fact_check = self.fact_check_repository.get_fact_check_by_claim_id(
            self.claim_without_check.id)
        
        self.assertIsNone(fact_check)

    def test_create_fact_check_source(self):
        """Test creating a fact check source"""
        source = self.fact_check_repository.create_fact_check_source(
            fact_check_id=self.fact_check.id,
            url="https://example.com/earth",
            title="Example Earth Page",
            description="An example Earth information page",
            relevance_score=0.85
        )
        
        self.assertIsNotNone(source.id)
        self.assertEqual(source.fact_check_id, self.fact_check.id)
        self.assertEqual(source.url, "https://example.com/earth")
        self.assertEqual(source.title, "Example Earth Page")
        self.assertEqual(source.description, "An example Earth information page")
        self.assertEqual(source.relevance_score, 0.85)

    def test_create_fact_check_source_minimal(self):
        """Test creating a fact check source with only required fields"""
        source = self.fact_check_repository.create_fact_check_source(
            fact_check_id=self.fact_check.id,
            url="https://minimal.com"
        )
        
        self.assertIsNotNone(source.id)
        self.assertEqual(source.fact_check_id, self.fact_check.id)
        self.assertEqual(source.url, "https://minimal.com")
        self.assertIsNone(source.title)
        self.assertIsNone(source.description)
        self.assertIsNone(source.relevance_score)

    def test_fact_check_deletion_cascade(self):
        """Test that deleting a fact check also deletes its sources"""
        fact_check_id = self.fact_check.id

        self.fact_check.delete()

        sources = FactCheckSource.objects.filter(fact_check_id=fact_check_id)
        self.assertEqual(len(sources), 0)
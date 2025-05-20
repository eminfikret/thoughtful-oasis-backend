from django.test import TestCase

from claims.models import Claim, FactCheck, FactCheckSource
from claims.repositories import ClaimRepository, FactCheckRepository


class ClaimRepositoryTest(TestCase):
    """Tests for the ClaimRepository class"""
    
    def setUp(self):
        self.claim_repo = ClaimRepository()
        
        self.claim_data = {
            'content_fragment': 'Test claim content',
            'content_position': {'start': 0, 'end': 18},
            'post_id': 123
        }
        
        self.standalone_claim = Claim.objects.create(
            content_fragment='Standalone claim',
            content_position={'start': 0, 'end': 15}
        )
        
        self.post_claim = Claim.objects.create(
            post_id=42,
            content_fragment='Post claim',
            content_position={'start': 5, 'end': 15}
        )
        
        self.comment_claim = Claim.objects.create(
            comment_id=24,
            content_fragment='Comment claim',
            content_position={'start': 3, 'end': 16}
        )
    
    def test_create_claim(self):
        """Test creating a claim through the repository"""
        claim = self.claim_repo.create_claim(self.claim_data)
        
        self.assertEqual(claim.content_fragment, 'Test claim content')
        self.assertEqual(claim.post_id, 123)
        self.assertIsNone(claim.comment_id)
        self.assertEqual(claim.content_position, {'start': 0, 'end': 18})
        
        db_claim = Claim.objects.get(id=claim.id)
        self.assertEqual(db_claim.content_fragment, 'Test claim content')
    
    def test_get_claim_by_id(self):
        """Test retrieving a claim by ID"""

        claim = self.claim_repo.get_claim_by_id(self.standalone_claim.id)
        self.assertEqual(claim.id, self.standalone_claim.id)
        self.assertEqual(claim.content_fragment, 'Standalone claim')
        
        claim = self.claim_repo.get_claim_by_id(99999)
        self.assertIsNone(claim)
    
    def test_get_claims_for_post(self):
        """Test getting claims for a specific post"""

        Claim.objects.create(
            post_id=42,
            content_fragment='Another post claim',
            content_position={'start': 20, 'end': 38}
        )

        claims = self.claim_repo.get_claims_for_post(42)
        
        self.assertEqual(len(claims), 2)
        self.assertTrue(all(c.post_id == 42 for c in claims))

        claims = self.claim_repo.get_claims_for_post(999)
        self.assertEqual(len(claims), 0)
    
    def test_get_claims_for_comment(self):
        """Test getting claims for a specific comment"""

        Claim.objects.create(
            comment_id=24,
            content_fragment='Another comment claim',
            content_position={'start': 25, 'end': 45}
        )
        

        claims = self.claim_repo.get_claims_for_comment(24)

        self.assertEqual(len(claims), 2)
        self.assertTrue(all(c.comment_id == 24 for c in claims))

        claims = self.claim_repo.get_claims_for_comment(999)
        self.assertEqual(len(claims), 0)


class FactCheckRepositoryTest(TestCase):
    """Tests for the FactCheckRepository class"""
    
    def setUp(self):
        self.fact_check_repo = FactCheckRepository()
        
        self.claim = Claim.objects.create(
            content_fragment='Test claim',
            content_position={'start': 0, 'end': 10}
        )
        
        self.fact_check_data = {
            'claim': self.claim,
            'verdict': 'supported',
            'summary': 'This claim is supported by evidence'
        }
        
        self.sources_data = [
            {
                'url': 'https://example.com/source1',
                'title': 'Source 1',
                'description': 'Description of source 1',
                'relevance_score': 0.85
            },
            {
                'url': 'https://example.com/source2',
                'title': 'Source 2',
                'description': 'Description of source 2',
                'relevance_score': 0.75
            }
        ]
    
    def test_create_fact_check(self):
        """Test creating a fact check through the repository"""
        fact_check = self.fact_check_repo.create_fact_check(self.fact_check_data)
        
        self.assertEqual(fact_check.claim, self.claim)
        self.assertEqual(fact_check.verdict, 'supported')
        self.assertEqual(fact_check.summary, 'This claim is supported by evidence')
        
        db_fact_check = FactCheck.objects.get(id=fact_check.id)
        self.assertEqual(db_fact_check.verdict, 'supported')
    
    def test_create_fact_check_with_sources(self):
        """Test creating a fact check with sources in a transaction"""
        fact_check = self.fact_check_repo.create_fact_check_with_sources(
            self.fact_check_data, self.sources_data
        )

        self.assertEqual(fact_check.claim, self.claim)
        self.assertEqual(fact_check.verdict, 'supported')

        sources = FactCheckSource.objects.filter(fact_check=fact_check)
        self.assertEqual(sources.count(), 2)

        source_urls = [source.url for source in sources]
        self.assertIn('https://example.com/source1', source_urls)
        self.assertIn('https://example.com/source2', source_urls)
    
    def test_get_fact_check_by_id(self):
        """Test retrieving a fact check by ID"""
        fact_check = self.fact_check_repo.create_fact_check(self.fact_check_data)

        retrieved = self.fact_check_repo.get_fact_check_by_id(fact_check.id)
        self.assertEqual(retrieved.id, fact_check.id)
        self.assertEqual(retrieved.verdict, 'supported')
        
        retrieved = self.fact_check_repo.get_fact_check_by_id(99999)
        self.assertIsNone(retrieved)
    
    def test_get_fact_checks_for_claim(self):
        """Test getting fact checks for a specific claim"""

        self.fact_check_repo.create_fact_check({
            'claim': self.claim,
            'verdict': 'supported',
            'summary': 'First fact check'
        })
        
        self.fact_check_repo.create_fact_check({
            'claim': self.claim,
            'verdict': 'contradicted',
            'summary': 'Second fact check'
        })
        

        fact_checks = self.fact_check_repo.get_fact_checks_for_claim(self.claim.id)
        
        self.assertEqual(fact_checks.count(), 2)
        self.assertTrue(all(fc.claim_id == self.claim.id for fc in fact_checks))

        verdicts = [fc.verdict for fc in fact_checks]
        self.assertIn('supported', verdicts)
        self.assertIn('contradicted', verdicts)

        other_claim = Claim.objects.create(content_fragment='Other claim')
        fact_checks = self.fact_check_repo.get_fact_checks_for_claim(other_claim.id)
        self.assertEqual(fact_checks.count(), 0)
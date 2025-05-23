from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Claim, FactCheck, FactCheckSource
from ..serializers import (
    ClaimSerializer,
    ClaimWithFactCheckSerializer,
    FactCheckSerializer,
    FactCheckSourceSerializer,
    TextSubmissionSerializer,
)

User = get_user_model()


class FactCheckSourceSerializerTest(TestCase):
    """Tests for the FactCheckSource serializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Test claim",
            claim_index=0,
            source_type="raw"
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="supported",
            summary="Test summary"
        )
        
        self.source_attributes = {
            'fact_check': self.fact_check,
            'url': 'https://example.com',
            'title': 'Example Source',
            'description': 'This is a test source',
            'relevance_score': 0.95
        }
        
        self.source = FactCheckSource.objects.create(**self.source_attributes)
    
    def test_serialization_with_all_fields(self):
        """Test serializing a source with all fields populated"""
        serializer = FactCheckSourceSerializer(self.source)
        data = serializer.data
        
        self.assertEqual(data['id'], self.source.id)
        self.assertEqual(data['url'], 'https://example.com')
        self.assertEqual(data['title'], 'Example Source')
        self.assertEqual(data['description'], 'This is a test source')
        self.assertEqual(data['relevance_score'], 0.95)
    
    def test_serialization_with_only_required_fields(self):
        """Test serializing a source with only required fields"""
        minimal_source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url='https://minimal-example.com'
        )
        
        serializer = FactCheckSourceSerializer(minimal_source)
        data = serializer.data
        
        self.assertEqual(data['url'], 'https://minimal-example.com')
        self.assertIsNone(data['title'])
        self.assertIsNone(data['description'])
        self.assertIsNone(data['relevance_score'])
    
    def test_deserialization_with_valid_data(self):
        """Test deserializing valid source data"""
        data = {
            'url': 'https://new-source.com',
            'title': 'New Source',
            'description': 'A brand new source',
            'relevance_score': 0.85
        }
        
        serializer = FactCheckSourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['url'], 'https://new-source.com')
        self.assertEqual(serializer.validated_data['title'], 'New Source')
        self.assertEqual(serializer.validated_data['description'], 'A brand new source')
        self.assertEqual(serializer.validated_data['relevance_score'], 0.85)
    
    def test_deserialization_with_only_required_fields(self):
        """Test deserializing with only required fields"""
        data = {
            'url': 'https://minimal.com',
        }
        
        serializer = FactCheckSourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['url'], 'https://minimal.com')
    
    def test_validation_invalid_url(self):
        """Test validation with invalid URL"""
        data = {
            'url': 'not-a-valid-url',
            'title': 'Invalid URL Source'
        }
        
        serializer = FactCheckSourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('url', serializer.errors)


class FactCheckSerializerTest(TestCase):
    """Tests for the FactCheck serializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Test claim",
            claim_index=0,
            source_type="raw"
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="supported",
            summary="Test summary"
        )
        
        self.source1 = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url='https://example1.com',
            title='Example Source 1',
            relevance_score=0.95
        )
        
        self.source2 = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url='https://example2.com',
            title='Example Source 2',
            relevance_score=0.85
        )
    
    def test_serialization_with_sources(self):
        """Test serializing a fact check with sources"""
        serializer = FactCheckSerializer(self.fact_check)
        data = serializer.data
        
        self.assertEqual(data['id'], self.fact_check.id)
        self.assertEqual(data['verdict'], 'supported')
        self.assertEqual(data['summary'], 'Test summary')
        self.assertEqual(len(data['sources']), 2)
        self.assertEqual(data['sources'][0]['url'], 'https://example1.com')
        self.assertEqual(data['sources'][1]['url'], 'https://example2.com')
    
    def test_serialization_without_sources(self):
        """Test serializing a fact check without sources"""

        FactCheckSource.objects.filter(fact_check=self.fact_check).delete()
        
        serializer = FactCheckSerializer(self.fact_check)
        data = serializer.data
        
        self.assertEqual(data['verdict'], 'supported')
        self.assertEqual(data['summary'], 'Test summary')
        self.assertEqual(len(data['sources']), 0)
    
    def test_deserialization_with_valid_data(self):
        """Test deserializing valid fact check data"""
        data = {
            'verdict': 'contradicted',
            'summary': 'This is a contradicted claim'
        }
        
        serializer = FactCheckSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['verdict'], 'contradicted')
        self.assertEqual(serializer.validated_data['summary'], 'This is a contradicted claim')
    
    def test_validation_missing_required_fields(self):
        """Test validation with missing required fields"""

        data1 = {
            'summary': 'Missing verdict'
        }
        serializer1 = FactCheckSerializer(data=data1)
        self.assertFalse(serializer1.is_valid())
        self.assertIn('verdict', serializer1.errors)

        data2 = {
            'verdict': 'supported'
        }
        serializer2 = FactCheckSerializer(data=data2)
        self.assertFalse(serializer2.is_valid())
        self.assertIn('summary', serializer2.errors)


class ClaimSerializerTest(TestCase):
    """Tests for the Claim serializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.raw_claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Raw text claim",
            claim_index=0,
            source_type="raw",
            source_text="This is a raw text source"
        )

        self.post_claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Post claim",
            claim_index=0,
            source_type="post",
            post_id=123
        )

        self.comment_claim = Claim.objects.create(
            user=self.user,
            extracted_claim="Comment claim",
            claim_index=0,
            source_type="comment",
            comment_id=456
        )
    
    def test_serialization_raw_text_claim(self):
        """Test serializing a raw text claim"""
        serializer = ClaimSerializer(self.raw_claim)
        data = serializer.data
        
        self.assertEqual(data['id'], self.raw_claim.id)
        self.assertEqual(data['extracted_claim'], "Raw text claim")
        self.assertEqual(data['source_type'], "raw")
        self.assertEqual(data['source_text'], "This is a raw text source")
        self.assertIsNone(data['post_id'])
        self.assertIsNone(data['comment_id'])
    
    def test_serialization_post_claim(self):
        """Test serializing a post claim"""
        serializer = ClaimSerializer(self.post_claim)
        data = serializer.data
        
        self.assertEqual(data['extracted_claim'], "Post claim")
        self.assertEqual(data['source_type'], "post")
        self.assertEqual(data['post_id'], 123)
        self.assertIsNone(data['comment_id'])
        self.assertIsNone(data['source_text'])
    
    def test_serialization_comment_claim(self):
        """Test serializing a comment claim"""
        serializer = ClaimSerializer(self.comment_claim)
        data = serializer.data
        
        self.assertEqual(data['extracted_claim'], "Comment claim")
        self.assertEqual(data['source_type'], "comment")
        self.assertEqual(data['comment_id'], 456)
        self.assertIsNone(data['post_id'])
        self.assertIsNone(data['source_text'])


class ClaimWithFactCheckSerializerTest(TestCase):
    """Tests for the ClaimWithFactCheck serializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.claim_with_check = Claim.objects.create(
            user=self.user,
            extracted_claim="Claim with fact check",
            claim_index=0,
            source_type="raw"
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim_with_check,
            verdict="supported",
            summary="This claim is supported"
        )
        
        self.source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://example.com",
            title="Example Source"
        )

        self.claim_without_check = Claim.objects.create(
            user=self.user,
            extracted_claim="Claim without fact check",
            claim_index=1,
            source_type="raw"
        )
    
    def test_serialization_with_fact_check(self):
        """Test serializing a claim with its fact check"""
        data = {
            "claim": self.claim_with_check,
            "fact_check": self.fact_check
        }
        serializer = ClaimWithFactCheckSerializer(data)
        result = serializer.data
        
        self.assertEqual(result['claim']['id'], self.claim_with_check.id)
        self.assertEqual(result['claim']['extracted_claim'], "Claim with fact check")
        self.assertEqual(result['fact_check']['id'], self.fact_check.id)
        self.assertEqual(result['fact_check']['verdict'], "supported")
        self.assertEqual(len(result['fact_check']['sources']), 1)
        self.assertEqual(result['fact_check']['sources'][0]['url'], "https://example.com")
    
    def test_serialization_without_fact_check(self):
        """Test serializing a claim without a fact check"""
        data = {
            "claim": self.claim_without_check,
            "fact_check": None
        }
        serializer = ClaimWithFactCheckSerializer(data)
        result = serializer.data
        
        self.assertEqual(result['claim']['id'], self.claim_without_check.id)
        self.assertEqual(result['claim']['extracted_claim'], "Claim without fact check")
        self.assertIsNone(result['fact_check'])


class TextSubmissionSerializerTest(TestCase):
    """Tests for the TextSubmission serializer"""
    
    def test_serialization_with_valid_text(self):
        """Test serializing valid text submission"""
        data = {"text": "This is a test text to be analyzed."}
        serializer = TextSubmissionSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['text'], "This is a test text to be analyzed.")
    
    def test_validation_missing_text(self):
        """Test validation with missing text field"""
        data = {}
        serializer = TextSubmissionSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('text', serializer.errors)
    
    def test_validation_empty_text(self):
        """Test validation with empty text field"""
        data = {"text": ""}
        serializer = TextSubmissionSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('text', serializer.errors)
    
    def test_validation_text_too_long(self):
        """Test validation with text exceeding max length"""
        long_text = "x" * 10001
        data = {"text": long_text}
        serializer = TextSubmissionSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('text', serializer.errors)
from django.test import TestCase
from django.contrib.auth.models import User

from claims.models import Claim, FactCheck, FactCheckSource
from claims.serializers import (
    ClaimModelSerializer,
    ClaimSerializer,
    FactCheckSerializer,
    FactCheckSourceSerializer,
    ClaimWithFactCheckSerializer,
    TextSubmissionSerializer,
)


class ClaimSerializerTest(TestCase):
    """Tests for the ClaimSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="The Earth is round",
            claim_index=1,
            source_type="raw",
            source_text="Original text"
        )
    
    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'content': "The Great Wall of China is visible from the Moon",
            'content_position': {"start": 0, "end": 49}
        }
        serializer = ClaimSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['content'], data['content'])
        self.assertEqual(serializer.validated_data['content_position'], data['content_position'])
    
    def test_missing_required_field(self):
        """Test serializer with missing required field"""
        data = {
            'content_position': {"start": 0, "end": 49}
        }
        serializer = ClaimSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
    
    def test_default_content_position(self):
        """Test that content_position defaults to None if not provided"""
        data = {
            'content': "The Great Wall of China is visible from the Moon"
        }
        serializer = ClaimSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data.get('content_position'))
    
    def test_serializer_output(self):
        """Test the serializer output for a claim instance"""
        serializer = ClaimSerializer(self.claim)
        data = serializer.data
        
        self.assertEqual(data['id'], self.claim.id)
        self.assertEqual(data['extracted_claim'], "The Earth is round")
        self.assertEqual(data['claim_index'], 1)
        self.assertEqual(data['source_type'], "raw")
        self.assertEqual(data['source_text'], "Original text")
        self.assertIsNone(data['post_id'])
        self.assertIsNone(data['comment_id'])
        self.assertIn('created_at', data)


class TextSubmissionSerializerTest(TestCase):
    """Tests for the TextSubmissionSerializer"""
    
    def test_valid_submission(self):
        """Test valid text submission"""
        data = {
            'text': "This is a valid text submission for fact checking."
        }
        serializer = TextSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['text'], data['text'])
    
    def test_empty_text(self):
        """Test empty text submission"""
        data = {'text': ""}
        serializer = TextSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['text'], "")
    
    def test_text_too_long(self):
        """Test text submission exceeding max length"""
        data = {'text': "a" * 10001}  # Exceeds the 10000 char limit
        serializer = TextSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('text', serializer.errors)
    
    def test_missing_text(self):
        """Test missing text field"""
        data = {}
        serializer = TextSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('text', serializer.errors)


class ClaimWithFactCheckSerializerTest(TestCase):
    """Tests for the ClaimWithFactCheckSerializer"""
    
    def setUp(self):

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        self.claim = Claim.objects.create(
            user=self.user,
            extracted_claim="The Earth is round",
            claim_index=1,
            source_type="raw",
            source_text="Original text"
        )

        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="supported",
            summary="Scientific evidence supports that the Earth is round"
        )

        self.source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://example.com/earth",
            title="Earth Facts",
            description="Scientific evidence about Earth's shape",
            relevance_score=0.95
        )
    
    def test_serialization_with_fact_check(self):
        """Test serializing a claim with its fact check"""
        data = {
            'claim': self.claim,
            'fact_check': self.fact_check
        }
        
        serializer = ClaimWithFactCheckSerializer(data)
        result = serializer.data

        self.assertEqual(result['claim']['id'], self.claim.id)
        self.assertEqual(result['claim']['extracted_claim'], "The Earth is round")

        self.assertEqual(result['fact_check']['id'], self.fact_check.id)
        self.assertEqual(result['fact_check']['verdict'], "supported")
        self.assertEqual(result['fact_check']['summary'], 
                        "Scientific evidence supports that the Earth is round")

        self.assertEqual(len(result['fact_check']['sources']), 1)
        self.assertEqual(result['fact_check']['sources'][0]['url'], "https://example.com/earth")
    
    def test_serialization_without_fact_check(self):
        """Test serializing a claim without a fact check"""

        claim_no_check = Claim.objects.create(
            user=self.user,
            extracted_claim="Water boils at 100C",
            claim_index=2,
            source_type="raw",
            source_text="Original text"
        )
        
        data = {
            'claim': claim_no_check,
            'fact_check': None
        }
        
        serializer = ClaimWithFactCheckSerializer(data)
        result = serializer.data

        self.assertEqual(result['claim']['id'], claim_no_check.id)
        self.assertEqual(result['claim']['extracted_claim'], "Water boils at 100C")

        self.assertIsNone(result['fact_check'])

class FactCheckSourceSerializerTest(TestCase):
    """Tests for the FactCheckSourceSerializer"""
    
    def setUp(self):
        self.claim = Claim.objects.create(
            content_fragment="The Earth is flat",
            content_position={"start": 0, "end": 16}
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="contradicted",
            summary="The Earth is actually an oblate spheroid"
        )
        
        self.source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://wikipedia.com/facts",
            title="NASA Earth Facts",
            description="Scientific evidence about Earth's shape",
            relevance_score=0.95
        )
        

        self.source_data = {
            'url': "https://wikipedia.com/facts",
            'title': "Example Facts",
            'description': "Some description",
            'relevance_score': 0.75
        }
    
    def test_serialization(self):
        """Test serializing a FactCheckSource instance"""
        serializer = FactCheckSourceSerializer(self.source)
        data = serializer.data
        
        self.assertEqual(data['url'], "https://wikipedia.com/facts")
        self.assertEqual(data['title'], "NASA Earth Facts")
        self.assertEqual(data['description'], "Scientific evidence about Earth's shape")
        self.assertEqual(float(data['relevance_score']), 0.95)
        self.assertIn('id', data)
        self.assertIn('created_at', data)
    
    def test_deserialization(self):
        """Test deserializing to create a FactCheckSource"""
        serializer = FactCheckSourceSerializer(data=self.source_data)
        self.assertTrue(serializer.is_valid())
        
        self.assertEqual(serializer.validated_data['url'], "https://wikipedia.com/facts")
        self.assertEqual(serializer.validated_data['title'], "Example Facts")
        self.assertEqual(serializer.validated_data['relevance_score'], 0.75)


class FactCheckSerializerTest(TestCase):
    """Tests for the FactCheckSerializer"""
    
    def setUp(self):
        self.claim = Claim.objects.create(
            content_fragment="The Earth is flat",
            content_position={"start": 0, "end": 16}
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="contradicted",
            summary="The Earth is actually an oblate spheroid"
        )
        
        self.source = FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://wikipedia.com/facts",
            title="NASA Earth Facts"
        )
        
        self.fact_check_data = {
            'verdict': 'supported',
            'summary': 'This claim is supported by evidence'
        }
    
    def test_serialization(self):
        """Test serializing a FactCheck instance with nested sources"""
        serializer = FactCheckSerializer(self.fact_check)
        data = serializer.data
        
        self.assertEqual(data['verdict'], "contradicted")
        self.assertEqual(data['summary'], "The Earth is actually an oblate spheroid")
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        
        self.assertIn('sources', data)
        self.assertEqual(len(data['sources']), 1)
        self.assertEqual(data['sources'][0]['url'], "https://wikipedia.com/facts")
    
    def test_deserialization(self):
        """Test deserializing to create a FactCheck"""
        serializer = FactCheckSerializer(data=self.fact_check_data) 
        self.assertTrue(serializer.is_valid())
        
        self.assertEqual(serializer.validated_data['verdict'], "supported")
        self.assertEqual(serializer.validated_data['summary'], 
                         "This claim is supported by evidence")


class ClaimModelSerializerTest(TestCase):
    """Tests for the ClaimModelSerializer"""
    
    def setUp(self):

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        self.post_claim = Claim.objects.create(
            post_id=1,
            extracted_claim="The Earth is flat",
            claim_index=1,
            source_type="post",
            content_position={"start": 0, "end": 16},
            user=self.user
        )
        
        self.comment_claim = Claim.objects.create(
            comment_id=5,
            extracted_claim="Water is wet",
            claim_index=2,
            source_type="comment",
            content_position={"start": 0, "end": 12},
            user=self.user
        )
        
        self.raw_claim = Claim.objects.create(
            extracted_claim="The sky is blue",
            claim_index=3,
            source_type="raw",
            source_text="Original text about sky color",
            user=self.user
        )

        self.post_fact_check = FactCheck.objects.create(
            claim=self.post_claim,
            verdict="contradicted",
            summary="The Earth is actually an oblate spheroid"
        )

        self.post_source = FactCheckSource.objects.create(
            fact_check=self.post_fact_check,
            url="https://wikipedia.com/facts",
            title="NASA Earth Facts"
        )
    
    def test_serialization_with_fact_checks(self):
        """Test serializing a Claim instance with nested fact checks and sources"""
        serializer = ClaimModelSerializer(self.post_claim)
        data = serializer.data
        
        self.assertEqual(data['extracted_claim'], "The Earth is flat")
        self.assertEqual(data['post_id'], 1)
        self.assertIsNone(data['comment_id'])
        self.assertEqual(data['content_position'], {"start": 0, "end": 16})
        self.assertIn('id', data)
        self.assertIn('created_at', data)

        self.assertIn('fact_checks', data)
        self.assertEqual(len(data['fact_checks']), 1)
        self.assertEqual(data['fact_checks'][0]['verdict'], "contradicted")

        self.assertIn('sources', data['fact_checks'][0])
        self.assertEqual(len(data['fact_checks'][0]['sources']), 1)
        self.assertEqual(data['fact_checks'][0]['sources'][0]['url'], "https://wikipedia.com/facts")
    
    def test_serialization_comment_claim(self):
        """Test serializing a comment-based claim"""
        serializer = ClaimModelSerializer(self.comment_claim)
        data = serializer.data
        
        self.assertEqual(data['extracted_claim'], "Water is wet")
        self.assertEqual(data['comment_id'], 5)
        self.assertIsNone(data['post_id'])
        self.assertEqual(data['source_type'], "comment")
        self.assertEqual(data['fact_checks'], []) 
    
    def test_serialization_raw_claim(self):
        """Test serializing a raw text claim"""
        serializer = ClaimModelSerializer(self.raw_claim)
        data = serializer.data
        
        self.assertEqual(data['extracted_claim'], "The sky is blue")
        self.assertEqual(data['source_type'], "raw")
        self.assertEqual(data['source_text'], "Original text about sky color")
        self.assertIsNone(data['post_id'])
        self.assertIsNone(data['comment_id'])
        self.assertEqual(data['fact_checks'], [])
    
    def test_serialization_multiple_claims(self):
        """Test serializing multiple claims"""
        claims = Claim.objects.all()
        serializer = ClaimModelSerializer(claims, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 3) 

        claim_texts = [item['extracted_claim'] for item in data]
        self.assertIn("The Earth is flat", claim_texts)
        self.assertIn("Water is wet", claim_texts)
        self.assertIn("The sky is blue", claim_texts)
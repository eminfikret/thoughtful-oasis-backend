from django.test import TestCase

from claims.models import Claim, FactCheck, FactCheckSource
from claims.serializers import (
    ClaimSerializer, ClaimModelSerializer,
    FactCheckSerializer, FactCheckSourceSerializer
)


class ClaimSerializerTest(TestCase):
    """Tests for the ClaimSerializer"""
    
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
            url="https://wikipedia/wiki",
            title="NASA Earth Facts",
            description="Scientific evidence about Earth's shape",
            relevance_score=0.95
        )
        
        self.source_data = {
            'url': "https://wikipedia/wiki",
            'title': "Example Facts",
            'description': "Some description",
            'relevance_score': 0.75
        }
    
    def test_serialization(self):
        """Test serializing a FactCheckSource instance"""
        serializer = FactCheckSourceSerializer(self.source)
        data = serializer.data
        
        self.assertEqual(data['url'], "https://wikipedia/wiki")
        self.assertEqual(data['title'], "NASA Earth Facts")
        self.assertEqual(data['description'], "Scientific evidence about Earth's shape")
        self.assertEqual(float(data['relevance_score']), 0.95)
        self.assertIn('id', data)
        self.assertIn('created_at', data)
    
    def test_deserialization(self):
        """Test deserializing to create a FactCheckSource"""
        serializer = FactCheckSourceSerializer(data=self.source_data)
        self.assertTrue(serializer.is_valid())
        
        self.assertEqual(serializer.validated_data['url'], "https://wikipedia/wiki")
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
            url="https://wikipedia/wiki",
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
        
        # Check that sources are included
        self.assertIn('sources', data)
        self.assertEqual(len(data['sources']), 1)
        self.assertEqual(data['sources'][0]['url'], "https://wikipedia/wiki")
    
    def test_deserialization(self):
        """Test deserializing to create a FactCheck"""
        serializer = FactCheckSerializer(data=self.fact_check_data)
        self.assertTrue(serializer.is_valid())
        
        # Cannot save without claim, just validate fields
        self.assertEqual(serializer.validated_data['verdict'], "supported")
        self.assertEqual(serializer.validated_data['summary'], "This claim is supported by evidence")


class ClaimModelSerializerTest(TestCase):
    """Tests for the ClaimModelSerializer"""
    
    def setUp(self):
        self.claim = Claim.objects.create(
            post_id=1,
            content_fragment="The Earth is flat",
            content_position={"start": 0, "end": 16}
        )
        
        self.fact_check = FactCheck.objects.create(
            claim=self.claim,
            verdict="contradicted",
            summary="The Earth is actually an oblate spheroid"
        )
        
        FactCheckSource.objects.create(
            fact_check=self.fact_check,
            url="https://wikipedia/wiki",
            title="NASA Earth Facts"
        )
    
    def test_serialization_with_fact_checks(self):
        """Test serializing a Claim instance with nested fact checks and sources"""
        serializer = ClaimModelSerializer(self.claim)
        data = serializer.data
        
        self.assertEqual(data['content_fragment'], "The Earth is flat")
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
        self.assertEqual(data['fact_checks'][0]['sources'][0]['url'], "https://wikipedia/wiki")
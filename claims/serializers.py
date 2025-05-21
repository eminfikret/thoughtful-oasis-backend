from rest_framework import serializers

from .models import Claim, FactCheck, FactCheckSource


class FactCheckSourceSerializer(serializers.Serializer):
    """Serializer for fact check sources"""
    id = serializers.IntegerField(read_only=True)
    url = serializers.URLField()
    title = serializers.CharField(allow_null=True, required=False)
    description = serializers.CharField(allow_null=True, required=False)
    relevance_score = serializers.FloatField(allow_null=True, required=False)


class FactCheckSerializer(serializers.Serializer):
    """Serializer for fact check results"""
    id = serializers.IntegerField(read_only=True)
    verdict = serializers.CharField()
    summary = serializers.CharField()
    sources = FactCheckSourceSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ClaimSerializer(serializers.Serializer):
    """Serializer for claims"""
    id = serializers.IntegerField(read_only=True)
    extracted_claim = serializers.CharField(read_only=True)
    claim_index = serializers.IntegerField(read_only=True)
    source_type = serializers.CharField(read_only=True)
    post_id = serializers.IntegerField(read_only=True, allow_null=True)
    comment_id = serializers.IntegerField(read_only=True, allow_null=True)
    source_text = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class ClaimWithFactCheckSerializer(serializers.Serializer):
    """Serializer for claims with fact check information"""
    claim = ClaimSerializer()
    fact_check = FactCheckSerializer(allow_null=True)


class TextSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting text for claim extraction and fact checking"""
    text = serializers.CharField(
        required=True,
        help_text='Text content to analyse for factual claims',
        max_length=10000 
    )
from rest_framework import serializers

from .models import FactualClaim, FactCheck, FactCheckSource


class FactCheckSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactCheckSource
        fields = ['id', 'url', 'title', 'description', 'relevance_score', 'created_at']
        read_only_fields = ['id', 'created_at']


class FactCheckSerializer(serializers.ModelSerializer):
    sources = FactCheckSourceSerializer(many=True, read_only=True)
    
    class Meta:
        model = FactCheck
        fields = ['id', 'verdict', 'summary', 'created_at', 'updated_at', 'sources']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FactualClaimSerializer(serializers.ModelSerializer):
    fact_checks = FactCheckSerializer(many=True, read_only=True)
    
    class Meta:
        model = FactualClaim
        fields = ['id', 'post_id', 'comment_id', 'content_fragment', 
                 'content_position', 'created_at', 'fact_checks']
        read_only_fields = ['id', 'created_at']


class ClaimSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting content to be checked for claims"""
    content = serializers.CharField(required=True)
    source_type = serializers.ChoiceField(choices=['post', 'comment'], required=True)
    source_id = serializers.IntegerField(required=True)
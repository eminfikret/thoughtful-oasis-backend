from rest_framework import serializers

from .models import Claim, FactCheck, FactCheckSource


class FactCheckSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactCheckSource
        fields = ['id', 'url', 'title', 'description', 'relevance_score', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'url': {'help_text': 'URL of the source used for fact-checking'},
            'title': {'help_text': 'Title of the source'},
            'description': {'help_text': 'Brief description of the source content'},
            'relevance_score': {'help_text': 'Score indicating relevance to the claim (0.0 to 1.0)'}
        }


class FactCheckSerializer(serializers.ModelSerializer):
    sources = FactCheckSourceSerializer(many=True, read_only=True)
    
    class Meta:
        model = FactCheck
        fields = ['id', 'verdict', 'summary', 'created_at', 'updated_at', 'sources']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'verdict': {
                'help_text': 'Fact check verdict: supported, contradicted, or unrelated'
            },
            'summary': {
                'help_text': 'Summary of the fact check findings based on sources'
            }
        }


class ClaimSerializer(serializers.Serializer):
    """Serializer for submitting a claim for verification"""
    content = serializers.CharField(
        required=True,
        help_text='The claim text to be fact-checked'
    )
    content_position = serializers.JSONField(
        required=False,
        default=None,
        help_text='Optional position data if this claim is extracted from a larger context'
    )


class ClaimModelSerializer(serializers.ModelSerializer):
    fact_checks = FactCheckSerializer(many=True, read_only=True)
    
    class Meta:
        model = Claim
        fields = ['id', 'post_id', 'comment_id', 'content_fragment', 
                 'content_position', 'created_at', 'fact_checks']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'post_id': {'help_text': 'ID of the post containing this claim, if applicable'},
            'comment_id': {'help_text': 'ID of the comment containing this claim, if applicable'},
            'content_fragment': {'help_text': 'The extracted claim text'},
        'content_position': {'help_text': 'Position markers of the claim in the original content'}
        }
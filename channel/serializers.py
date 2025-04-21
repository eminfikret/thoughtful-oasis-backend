from rest_framework import serializers

from .models import Channel


class ChannelSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'created_by', 'created_by_username', 'created_at']
        read_only_fields = ['created_by']
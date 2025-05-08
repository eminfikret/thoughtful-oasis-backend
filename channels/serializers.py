from rest_framework import serializers

from common.serializers import PaginationQueryParams

from .models import Channel


class ChannelSerializer(serializers.ModelSerializer):
    owner_id = serializers.PrimaryKeyRelatedField(source='owner', read_only=True)
    numb_of_subscribers = serializers.IntegerField(source='subscriptions.count', read_only=True)

    class Meta:
        model = Channel
        fields = [
            'id', 'name', 'description', 'slug', 'owner_id',
            'numb_of_subscribers', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'numb_of_subscribers', 'updated_at'
        ]

class ChannelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['name', 'description']

class ChannelUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False)

    class Meta:
        model = Channel
        fields = ['name', 'description']

class ChannelsQueryParamsSerializer(PaginationQueryParams):
    pass

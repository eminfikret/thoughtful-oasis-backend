from rest_framework import serializers
from django.contrib.auth.models import User

from common.serializers import PaginationQueryParams

from .models import Channel


class ChannelOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = fields

class ChannelSerializer(serializers.ModelSerializer):
    owner = ChannelOwnerSerializer(read_only=True)
    numb_of_subscribers = serializers.IntegerField(source='subscriptions.count', read_only=True)

    class Meta:
        model = Channel
        fields = [
            'id', 'name', 'description', 'slug', 'owner',
            'numb_of_subscribers', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'numb_of_subscribers', 'updated_at'
        ]

class ChannelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['name', 'description']
        # Disable automatic uniqueness validation on the 'name' field.
        # This allows us to handle duplicate name conflicts manually in the service layer
        # and return a proper 409 Conflict instead of DRF's default 400 Bad Request.
        extra_kwargs = {
            'name': {'validators': []},
        }

class ChannelUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False)

    class Meta:
        model = Channel
        fields = ['name', 'description']
        # Disable automatic uniqueness validation on the 'name' field.
        # This all ows us to handle duplicate name conflicts manually in the service layer
        # and return a proper 409 Conflict instead of DRF's default 400 Bad Request.
        extra_kwargs = {
            'name': {'validators': []},
        }

class ChannelsQueryParamsSerializer(PaginationQueryParams):
    search = serializers.CharField(required=False, allow_blank=True)
    pass

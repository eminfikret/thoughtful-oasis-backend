from django.contrib.auth.models import User
from rest_framework import serializers

from channels.models import Channel
from common.serializers import PaginationQueryParams

from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    channel_id = serializers.PrimaryKeyRelatedField(source='channel', read_only=True)
    subscriber_id = serializers.PrimaryKeyRelatedField(source='subscriber', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'channel_id', 'subscriber_id', 'created_at']
        read_only_fields = fields

class UserSummarySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source='date_joined')

    class Meta:
        model = User
        fields = ['id', 'username', 'created_at']
        read_only_fields = fields

class SubscriberSerializer(serializers.ModelSerializer):
    subscriber = UserSummarySerializer(read_only=True)
    subscribed_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Subscription
        fields = ['id', 'subscriber', 'subscribed_at']
        read_only_fields = fields

class ChannelSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'created_at']
        read_only_fields = fields

class MySubscriptionSerializer(serializers.ModelSerializer):
    channel = ChannelSummarySerializer(read_only=True)
    subscribed_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Subscription
        fields = ['id', 'channel', 'subscribed_at']
        read_only_fields = fields


class SubscribersQueryParamsSerializer(PaginationQueryParams):
    pass

class SubscriptionsQueryParamsSerializer(PaginationQueryParams):
    pass
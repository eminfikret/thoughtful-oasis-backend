from rest_framework import serializers

from common.serializers import PaginationQueryParams
from votes.repositories import VoteRepository

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    channel = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'channel', 'author', 'created_at', 'updated_at',
                   'votes']
        read_only_fields = ['id', 'channel', 'author', 'created_at', 'updated_at', 'votes']

    def get_votes(self, obj):
        return VoteRepository.get_post_votes(obj.id)
        
    def get_channel(self, obj):
        try:
            if hasattr(obj, 'channel') and obj.channel:
                return {
                    'id': obj.channel.id,
                    'name': obj.channel.name
                }
            return None
        except Exception:
            return None
        
    def get_author(self, obj):
        try:
            if hasattr(obj, 'author') and obj.author:
                return {
                    'id': obj.author.id,
                    'name': obj.author.username
                }
            return None
        except Exception:
            return None


class PostCreateSerializer(serializers.ModelSerializer):
    channel_id=serializers.IntegerField()
    class Meta:
        model = Post
        fields = ['title', 'content', 'channel_id']
        real_only_fields=['id', 'channel_id', 'created_at','updated_at']


class PostUpdateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=False, max_length=255)
    content = serializers.CharField(required=False)

    class Meta:
        model = Post
        fields = ['title', 'content']


class PostsQueryParamsSerializer(PaginationQueryParams):
    pass
from rest_framework import serializers

from common.serializers import PaginationQueryParams
from votes.repositories import VoteRepository

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_id = serializers.PrimaryKeyRelatedField(source='author', read_only=True)
    channel_id = serializers.PrimaryKeyRelatedField(source='channel', read_only=True)
    votes = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'channel_id', 'author_id', 'created_at', 'updated_at',
                   'votes']
        read_only_fields = ['id', 'channel_id', 'author_id', 'created_at', 'updated_at', 'votes']

    def get_votes(self, obj):
        return VoteRepository.get_post_votes(obj.id)


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
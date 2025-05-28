from rest_framework import serializers

from comments.models import Comment
from votes.repositories import VoteRepository


class CreateCommentSerializer(serializers.ModelSerializer):
    post_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ['id', 'post_id', 'author_id', 'content']

class ReplyCommentSerializer(serializers.ModelSerializer):
    parent_comment_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ['id', 'author_id','parent_comment_id', 'content']

class PostCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author_id', 'created_at', 'replies', 'votes']

    def get_replies(self, obj):
        replies = obj.children.all()
        return CommentReplySerializer(replies, many=True).data
        
    def get_votes(self, obj):
        return VoteRepository.get_comment_votes(obj.id)


class CommentReplySerializer(serializers.ModelSerializer):
    votes = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author_id', 'created_at', 'votes']
        
    def get_votes(self, obj):
        return VoteRepository.get_comment_votes(obj.id)
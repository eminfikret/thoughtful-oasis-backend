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

class CommentReplySerializer(serializers.ModelSerializer):
    votes = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    post_id = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'post_id', 'author', 'created_at', 'votes', 'parent_id']
        
    def get_votes(self, obj):
        return VoteRepository.get_comment_votes(obj.id)
        
    def get_author(self, obj):
        return {
            'id': obj.author.id,
            'name': obj.author.username
        }
        
    def get_post_id(self, obj):
        return obj.post.id

    def get_parent_id(self, obj):
        return obj.parent_comment_id 

class PostCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    post_id = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'post_id', 'author', 'created_at', 'replies', 'votes', 'parent_id']

    def get_replies(self, obj):
        replies = obj.children.all()
        return CommentReplySerializer(replies, many=True).data
        
    def get_votes(self, obj):
        return VoteRepository.get_comment_votes(obj.id)
        
    def get_author(self, obj):
        return {
            'id': obj.author.id,
            'name': obj.author.username
        }
        
    def get_post_id(self, obj):
        return obj.post.id
        
    def get_parent_id(self, obj):
        return obj.parent_comment_id 
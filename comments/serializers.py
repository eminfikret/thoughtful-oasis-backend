from rest_framework import serializers

from comments.models import Comment


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

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author_id', 'created_at', 'replies']

    def get_replies(self, obj):
        replies = obj.children.all()
        return CommentReplySerializer(replies, many=True).data

class CommentReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author_id', 'created_at']
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from comments.exceptions import CommentNotFound
from comments.models import Comment
from comments.repositories import CommentRepository
from posts.models import Post
from users.models import User


class CommentService:

    @staticmethod
    def create_comment(post_id: int, author: User, content: str) -> Comment:
        post = get_object_or_404(Post, id=post_id)
        return CommentRepository.create_comment(post, author, content)

    @staticmethod
    def create_reply(parent_comment_id: int, author: User, content: str) -> Comment:
        try:
            parent_comment = Comment.objects.get(pk=parent_comment_id)
        except Comment.DoesNotExist:
            raise CommentNotFound()

        comment = Comment.objects.create(
            post=parent_comment.post,
            author=author,
            content=content,
            parent_comment=parent_comment,
        )
        return comment

    @staticmethod
    def get_comments_for_post(post_id: int):
        return CommentRepository.get_comments_for_post(post_id)

    @staticmethod
    def get_replies_for_comment(comment_id: int):
        return CommentRepository.get_replies_for_comment(comment_id)

    @staticmethod
    def update_comment(comment_id: int, user: User, content: str) -> Comment:
        try:
            comment = Comment.objects.get(pk=comment_id)

            if comment.author != user:
                raise PermissionDenied("You can only update your own comments")

            comment.content = content
            comment.save()

            return comment
        except Comment.DoesNotExist:
            raise CommentNotFound()
            
    @staticmethod
    def get_user_comments(user_id: int, offset: int = 0, limit: int = 10):
        """Get comments made by a specific user with pagination"""
        get_object_or_404(User, id=user_id)
        comments = CommentRepository.get_comments_by_user(user_id, offset, limit)
        total = CommentRepository.count_user_comments(user_id)
        return comments, total
from posts.models import Post
from users.models import User
from comments.models import Comment
from comments.repositories import CommentRepository
from django.shortcuts import get_object_or_404
from comments.exceptions import CommentNotFound, InvalidReplyDepth

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

        if parent_comment.parent_comment_id is not None:
            raise InvalidReplyDepth()

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
from django.db.models import Prefetch

from .models import Comment


class CommentRepository:
    @staticmethod
    def create_comment(post, author, content):
        return Comment.objects.create(
            post=post,
            author=author,
            content=content,
            parent_comment=None
        )

    @staticmethod
    def create_reply(post, parent_comment, author, content):
        return Comment.objects.create(
            post=post,
            parent_comment=parent_comment,
            author=author,
            content=content
        )

    @staticmethod
    def get_comments_for_post(post_id):
        return Comment.objects.filter(
            post_id=post_id,
            parent_comment__isnull=True
        ).prefetch_related(
            Prefetch('children')
        ).select_related('author')

    @staticmethod
    def get_replies_for_comment(comment_id):
        return Comment.objects.filter(
            parent_comment_id=comment_id
        ).select_related('author')
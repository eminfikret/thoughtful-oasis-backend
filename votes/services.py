from django.contrib.auth.models import User

from comments.exceptions import CommentNotFound
from comments.models import Comment
from posts.exceptions import PostNotFoundException
from posts.models import Post

from .repositories import VoteRepository


class VoteService:
    @staticmethod
    def upvote_post(post_id: int, user: User) -> dict:
        """Upvote a post"""
        try:

            Post.objects.get(id=post_id)
            return VoteRepository.vote_post(post_id, user.id, is_upvote=True)
        except Post.DoesNotExist:
            raise PostNotFoundException(post_id)

    @staticmethod
    def downvote_post(post_id: int, user: User) -> dict:
        """Downvote a post"""
        try:
            Post.objects.get(id=post_id)
            return VoteRepository.vote_post(post_id, user.id, is_upvote=False)
        except Post.DoesNotExist:
            raise PostNotFoundException(post_id)

    @staticmethod
    def upvote_comment(comment_id: int, user: User) -> dict:
        """Upvote a comment"""
        try:

            Comment.objects.get(id=comment_id)
            return VoteRepository.vote_comment(comment_id, user.id, is_upvote=True)
        except Comment.DoesNotExist:
            raise CommentNotFound()

    @staticmethod
    def downvote_comment(comment_id: int, user: User) -> dict:
        """Downvote a comment"""
        try:

            Comment.objects.get(id=comment_id)
            return VoteRepository.vote_comment(comment_id, user.id, is_upvote=False)
        except Comment.DoesNotExist:
            raise CommentNotFound()

    @staticmethod
    def get_post_vote_status(post_id: int, user_id: int) -> dict:
        """Get a user's vote for a post and the total counts"""
        vote_status = VoteRepository.get_user_post_vote(post_id, user_id)
        counts = VoteRepository.get_post_votes(post_id)
        return {**vote_status, **counts}

    @staticmethod
    def get_comment_vote_status(comment_id: int, user_id: int) -> dict:
        """Get a user's vote for a comment and the total counts"""
        vote_status = VoteRepository.get_user_comment_vote(comment_id, user_id)
        counts = VoteRepository.get_comment_votes(comment_id)
        return {**vote_status, **counts}
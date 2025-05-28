from django.contrib.auth.models import User
from django.db import models

from comments.models import Comment
from common.models import BaseModel
from posts.models import Post


class PostVote(BaseModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='post_votes'
    )
    is_upvote = models.BooleanField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_votes'
        unique_together = ('post', 'user')
        verbose_name = 'Post Vote'
        verbose_name_plural = 'Post Votes'

    def __str__(self):
        vote_type = "Upvote" if self.is_upvote else "Downvote"
        return f"{vote_type} on {self.post.title} by {self.user.username}"


class CommentVote(BaseModel):
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_votes'
    )
    is_upvote = models.BooleanField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comment_votes'
        unique_together = ('comment', 'user')
        verbose_name = 'Comment Vote'
        verbose_name_plural = 'Comment Votes'

    def __str__(self):
        vote_type = "Upvote" if self.is_upvote else "Downvote"
        return f"{vote_type} on comment {self.comment.id} by {self.user.username}"
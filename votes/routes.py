from django.urls import path

from . import controllers

urlpatterns = [
    # Post voting
    path('posts/<int:post_id>/upvote/', controllers.upvote_post, name='upvote_post'),
    path('posts/<int:post_id>/downvote/', controllers.downvote_post, name='downvote_post'),
    path('posts/<int:post_id>/votes/', controllers.get_post_votes, name='get_post_votes'),
    
    # Comment voting
    path('comments/<int:comment_id>/upvote/', controllers.upvote_comment, name='upvote_comment'),
    path('comments/<int:comment_id>/downvote/', 
         controllers.downvote_comment, name='downvote_comment'),
    path('comments/<int:comment_id>/votes/', 
         controllers.get_comment_votes, name='get_comment_votes'),
]
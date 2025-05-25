from django.urls import path
from comments import controllers as comment_controllers

urlpatterns = [
    path('create/', comment_controllers.CreateCommentView.as_view(), name='create_comment'),
    path('reply/', comment_controllers.CreateReplyView.as_view(), name='create_reply'),
    path('', comment_controllers.PostCommentsView.as_view(), name='post_comments'),
    path('<int:comment_id>/replies/', comment_controllers.CommentRepliesView.as_view(), name='comment_replies'),
]
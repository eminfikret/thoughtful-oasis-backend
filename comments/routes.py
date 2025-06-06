from django.urls import path

from comments import controllers as comment_controllers

urlpatterns = [
    path('create/', comment_controllers.CreateCommentView.as_view(), name='create_comment'),
    path('reply/', comment_controllers.CreateReplyView.as_view(), name='create_reply'),
    path('', comment_controllers.PostCommentsView.as_view(), name='post_comments'),
    path('<int:comment_id>/replies/', comment_controllers.CommentRepliesView.as_view(),
         name='comment_replies'),
    path('<int:comment_id>/update/', comment_controllers.UpdateCommentView.as_view(), 
         name='update_comment'),
    path('user/', comment_controllers.UserCommentsView.as_view(), name='user_comments'),
]
from django.urls import path

from posts import controllers

urlpatterns = [
    path('', controllers.ChannelPostsController.list_posts, name='list_posts'),
    path('create/', controllers.ChannelPostsController.create_post, name='create_post'),
    path('<int:post_id>/', controllers.ChannelPostsController.as_view(), name='get_post'),
    path('<int:post_id>/update/', controllers.PostDetailController.as_view(), name='update_post'),
    path('<int:post_id>/delete/', controllers.ChannelPostsController.delete_post,
          name='delete_post'),
]
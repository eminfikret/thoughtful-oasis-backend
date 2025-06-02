from django.urls import path

from posts import controllers

urlpatterns = [
    path('', controllers.list_posts, name='list_posts'),
    path('create/', controllers.ChannelPostsController.create_post, name='create_post'),
    path('<int:post_id>/', controllers.ChannelPostsController.get_post, name='get_post'),
    path('<int:post_id>/update/', controllers.PostDetailController.as_view(), name='update_post'),
    path('<int:post_id>/delete/', controllers.delete_post, name='delete_post'),
]
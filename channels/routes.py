from django.urls import path

from channels import controllers as channel_controllers
from posts import controllers as post_controllers
from subscriptions import controllers as subscription_controllers

urlpatterns = [
    path(
        '',
        channel_controllers.ChannelListController.as_view(),
        name='channels'
    ),
    path(
        '<int:pk>/',
        channel_controllers.ChannelDetailController.as_view(),
        name='channel-detail'
    ),
    path(
        '<int:pk>/subscriptions',
        subscription_controllers.SubscribersListController.as_view(),
        name='channel-subscribers'
    ),
    path(
        '<int:pk>/subscribe',
        subscription_controllers.SubscribeController.as_view(),
        name='channel-subscribe'
    ),
    path(
        '<int:pk>/unsubscribe',
        subscription_controllers.UnsubscribeController.as_view(),
        name='channel-unsubscribe'
    ),
    path(
        '<int:pk>/posts/',
        post_controllers.ChannelPostsController.as_view(),
        name='get_posts_by_channel'),

]
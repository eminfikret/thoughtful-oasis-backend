from django.urls import path

from channels import controllers as channel_controllers
from subscriptions import controllers as subscription_controllers

urlpatterns = [
    path(
        '',
        channel_controllers.ChannelListController.as_view(),
        name='channel-list'
    ),
    path(
        '<int:channel_id>/',
        channel_controllers.ChannelDetailController.as_view(),
        name='channel-detail'
    ),
    path(
        '<int:channel_id>/subscriptions',
        subscription_controllers.SubscribersListController.as_view(),
        name='channel-subscribers'
    ),
    path(
        '<int:channel_id>/subscribe',
        subscription_controllers.SubscribeController.as_view(),
        name='channel-subscribe'
    ),
    path(
        '<int:channel_id>/unsubscribe',
        subscription_controllers.UnsubscribeController.as_view(),
        name='channel-unsubscribe'
    ),
]
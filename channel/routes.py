from django.urls import path

from . import controllers

urlpatterns = [
    path('', controllers.ChannelListController.as_view(), name='channel-list'),
]
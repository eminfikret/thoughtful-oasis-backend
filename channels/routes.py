from django.urls import path

from channels import controllers

urlpatterns = [
    path('', controllers.ChannelListController.as_view(), name='channels'),
    path('<int:pk>/', controllers.ChannelDetailController.as_view(), name='channel-detail'),
]
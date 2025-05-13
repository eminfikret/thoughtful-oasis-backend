from django.urls import path

from subscriptions import controllers

urlpatterns = [
    path('', controllers.MySubscriptionsController.as_view(), name='subscriptions'),
]
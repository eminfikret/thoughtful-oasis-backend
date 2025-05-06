from django.urls import path

from . import controllers

urlpatterns = [
    path('', controllers.UserListController.as_view(), name='user-list'),
    path('register/', controllers.RegisterController.as_view(), name='user-register'),
    path('login/', controllers.LoginController.as_view(), name='user-login'),
    path('<int:user_id>/', controllers.UserDetailController.as_view(), name='user-detail'),
    path('<int:user_id>/profile/', controllers.UserProfileController.as_view(), name='user-profile'),
]
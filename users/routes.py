from django.urls import path

from .controllers import (
    CheckUsernameEmailController,
    LoginController,
    RefreshTokenView,
    RegisterController,
    UserDetailController,
    UserListController,
    UserProfileController,
)

urlpatterns = [
    path('', UserListController.as_view(), name='user-list'),
    path('register/', RegisterController.as_view(), name='user-register'),
    path('login/', LoginController.as_view(), name='user-login'),
    path('tokenRefresh/', RefreshTokenView.as_view(), name='user-refresh-token'),

    path('<int:user_id>/', UserDetailController.as_view(), name='user-detail'),
    path(
        '<int:user_id>/profile/',
        UserProfileController.as_view(),
        name='user-profile'
    ),
    path('check-availability/', CheckUsernameEmailController.as_view(), name='check-availability'),
]
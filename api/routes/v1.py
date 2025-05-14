from django.urls import include, path

urlpatterns = [
    path('users/', include('users.routes')),
    path('channels/', include('channels.routes')),
    path('subscriptions/', include('subscriptions.routes')),
    path('claims/', include('claims.routes')),
]
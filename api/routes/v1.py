from django.urls import include, path

urlpatterns = [
    path('users/', include('users.routes')),
    path('channels/', include('channels.routes')),
    path('claims/', include('claims.routes')),
    path('posts/', include('posts.routes')),
    path('comments/', include('comments.routes')),
    path('claims/', include('claims.routes')),
]
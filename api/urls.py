from django.urls import include, path

urlpatterns = [
    path('v1/', include('api.routes.v1')),
]
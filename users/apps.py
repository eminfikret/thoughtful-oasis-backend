from datetime import timedelta

from django.apps import AppConfig
from rest_framework_simplejwt.settings import api_settings


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    def ready(self):
        api_settings.ACCESS_TOKEN_LIFETIME = timedelta(hours=1)
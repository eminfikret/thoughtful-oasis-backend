from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from .repositories import UserRepository
from jwt import decode as jwt_decode
from django.conf import settings
from datetime import datetime


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update the user profile when a user is created or updated."""
    repo = UserRepository()
    if created:
        repo.create_profile(instance)
    else:
        instance.profile.save()

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    def get_all_users(self):
        return self.user_repository.get_all_users()

    def get_user_by_id(self, user_id):
        return self.user_repository.get_user_by_id(user_id)

    def register_user(self, user_data):
        password = user_data.pop('password')
        user = self.user_repository.create_user({
            'username': user_data['username'],
            'email': user_data['email'],
            'password': password,
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', '')
        })
        return user
    
    def login_user(self, username, password):
        user = self.user_repository.authenticate_user(username, password)
        if not user:
            return None

        refresh = RefreshToken.for_user(user)

        access_token = str(refresh.access_token)

        decoded = jwt_decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
        exp_timestamp = decoded.get('exp')
        if exp_timestamp:
            exp_time = datetime.fromtimestamp(exp_timestamp)
            print(f"[DEBUG] Access token will expire at: {exp_time}")

        return {
            'user': user,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
        }

    def refresh_token(self, refresh_token_str):

        try:
            refresh_token = RefreshToken(refresh_token_str)
            new_access_token = str(refresh_token.access_token)

            # Optional debug: print expiry
            exp = refresh_token.access_token['exp']
            from datetime import datetime
            print("[DEBUG] Refreshed access token expires at:", datetime.fromtimestamp(exp))

            return {
                'access_token': new_access_token,
                'refresh_token': str(refresh_token),  # return same refresh if you don’t rotate
            }
        except TokenError as e:
            print("[ERROR] Invalid refresh token:", str(e))
            return None


    def update_user(self, user_id, user_data):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return None
        return self.user_repository.update_user(user, user_data)

    def get_user_profile(self, user_id):
        return self.user_repository.get_profile(user_id)

    def update_user_profile(self, user_id, profile_data):
        profile = self.user_repository.get_profile(user_id)
        if not profile:
            return None
        return self.user_repository.update_profile(profile, profile_data)

    def update_reputation(self, user_id, amount):
        return self.user_repository.update_user_reputation(user_id, amount)
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from jwt import decode as jwt_decode
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import UserProfile
from .repositories import UserRepository


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update the user profile when a user is created or updated."""
    repo = UserRepository()
    if created:
        try:
            UserProfile.objects.get(user=instance)
        except UserProfile.DoesNotExist:
            repo.create_profile(instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    def get_all_users(self):
        return self.user_repository.get_all_users()

    def get_user_by_id(self, user_id):
        return self.user_repository.get_user_by_id(user_id)

    def register_user(self, user_data):
        try:
            password = user_data.pop('password')
            user = self.user_repository.create_user({
                'username': user_data['username'],
                'email': user_data['email'], 
                'password': password,
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', '')
            })
            return user
        except KeyError as e:
        
            raise ValueError(f"Missing required field: {str(e)}")
    
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

            exp = refresh_token.access_token['exp']

            print("[DEBUG] Refreshed access token expires at:", datetime.fromtimestamp(exp))

            return {
                'access_token': new_access_token,
                'refresh_token': str(refresh_token), 
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
    
    def check_username_email_exists(self, username=None, email=None):
        """Check if a username or email already exists."""
        return self.user_repository.check_username_email_exists(username, email)

    def delete_user(self, user_id):
        """Delete a user by their ID."""
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return False
        user.delete()
        return True
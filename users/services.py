from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from .repositories import UserRepository
from .models import UserProfile


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
        
        token, _ = Token.objects.get_or_create(user=user)
        return {
            'user': user,
            'token': token.key
        }
    
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
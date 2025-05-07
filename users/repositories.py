from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .models import UserProfile


class UserRepository:
    @staticmethod
    def create_profile(user):
        """Create a new user profile."""
        return UserProfile.objects.create(user=user)

    def get_all_users(self):
        return User.objects.all()
    
    def get_user_by_username(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def create_user(self, user_data):
        return User.objects.create_user(**user_data)
    
    def authenticate_user(self, username, password):
        return authenticate(username=username, password=password)
    
    def update_user(self, user, user_data):
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save()
        return user
    
    def get_profile(self, user_id):
        try:
            return UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None
    
    def update_profile(self, profile, profile_data):
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        return profile
    
    def update_user_reputation(self, user_id, amount):
        profile = get_object_or_404(UserProfile, user_id=user_id)
        profile.reputation += amount
        profile.save()
        return profile
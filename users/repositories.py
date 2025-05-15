from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
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
        """Create a new user with password validation"""
        password = user_data.get('password')
        
        validate_password(password)

        return User.objects.create_user(**user_data)
    
    def authenticate_user(self, username, password):
        return authenticate(username=username, password=password)
    
    def update_user(self, user, update_data):
        """Update user fields"""
        # If password is being updated, validate it
        if 'password' in update_data:
            try:
                validate_password(update_data['password'])
                user.set_password(update_data.pop('password'))
            except ValidationError as e:
                raise e
        
        # Update other fields
        for key, value in update_data.items():
            setattr(user, key, value)
        
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
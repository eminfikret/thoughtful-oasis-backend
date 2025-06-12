from typing import List, Optional

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404

from common.params import PaginationParams

from .models import UserProfile


class UserRepository:
    @staticmethod
    def create_profile(user):
        """Create a new user profile."""
        return UserProfile.objects.create(user=user)

    @staticmethod
    def get_all_users(
        search: Optional[str] = None, 
        pagination: Optional[PaginationParams] = None
    ) -> List[User]:
        """
        Get all users with optional search and pagination
        """
        pagination = pagination or PaginationParams()
        queryset = User.objects.all()

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        return list(queryset[pagination.offset:pagination.offset + pagination.limit])
    
    @staticmethod
    def get_users_count(search: Optional[str] = None) -> int:
        """
        Returns total count of User records.
        Optional filtering by search term.
        """
        queryset = User.objects.all()

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        return queryset.count()
    
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
        if 'password' in update_data:
            try:
                validate_password(update_data['password'])
                user.set_password(update_data.pop('password'))
            except ValidationError as e:
                raise e
        
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
    
    def check_username_email_exists(self, username=None, email=None):
        """Check if a username or email already exists in the system."""
        result = {
            'username_exists': False,
            'email_exists': False
        }
        
        if username:

            result['username_exists'] = User.objects.filter(username__iexact=username).exists()
        
        if email:
            result['email_exists'] = User.objects.filter(email__iexact=email).exists()
        
        return result
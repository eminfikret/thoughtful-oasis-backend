from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class UserRepository:
    def get_all_users(self):
        return User.objects.all()
    
    def get_user_by_username(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    def create_user(self, user_data):
        return User.objects.create_user(**user_data)
    
    def authenticate_user(self, username, password):
        return authenticate(username=username, password=password)
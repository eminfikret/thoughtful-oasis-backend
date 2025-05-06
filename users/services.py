from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from .repositories import UserRepository


class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    def get_all_users(self):
        return self.user_repository.get_all_users()
    
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

        return {
            'user': user.username,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
        }
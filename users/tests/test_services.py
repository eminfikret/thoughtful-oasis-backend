from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token

from users.models import UserProfile
from users.services import UserService


class UserServiceTest(TestCase):
    def setUp(self):
        self.service = UserService()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )
        self.profile = UserProfile.objects.get(user=self.test_user)
    
    def test_signal_handler_creates_profile(self):
        self.assertIsNotNone(self.test_user.profile)
        self.assertEqual(self.test_user.profile.user, self.test_user)
    
    def test_get_all_users(self):
        users = self.service.get_all_users()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.test_user)
    
    def test_get_user_by_id_existing(self):
        user = self.service.get_user_by_id(self.test_user.id)
        self.assertEqual(user, self.test_user)
    
    def test_get_user_by_id_non_existing(self):
        user = self.service.get_user_by_id(999)
        self.assertIsNone(user)
    
    def test_register_user(self):
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        new_user = self.service.register_user(user_data)
        self.assertEqual(new_user.username, 'newuser')
        self.assertEqual(new_user.email, 'new@example.com')
        self.assertEqual(new_user.first_name, 'New')
        self.assertEqual(new_user.last_name, 'User')
        
        self.assertIsNotNone(UserProfile.objects.filter(user=new_user).first())
    
    def test_login_user_valid(self):
        result = self.service.login_user('testuser', 'password123')
        self.assertEqual(result['user'], self.test_user)
        self.assertIsNotNone(result['token'])
        self.assertIsInstance(result['token'], str)
        
        self.assertTrue(Token.objects.filter(user=self.test_user).exists())
    
    def test_login_user_invalid(self):
        result = self.service.login_user('testuser', 'wrongpassword')
        self.assertIsNone(result)
    
    def test_update_user(self):
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        updated_user = self.service.update_user(self.test_user.id, update_data)
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.email, 'updated@example.com')
    
    def test_update_user_non_existing(self):
        updated_user = self.service.update_user(999, {'first_name': 'Updated'})
        self.assertIsNone(updated_user)
    
    def test_get_user_profile_existing(self):
        profile = self.service.get_user_profile(self.test_user.id)
        self.assertEqual(profile, self.profile)
    
    def test_get_user_profile_non_existing(self):
        profile = self.service.get_user_profile(999)
        self.assertIsNone(profile)
    
    def test_update_user_profile(self):
        profile_data = {
            'bio': 'Updated bio',
            'website': 'https://updated.com'
        }
        updated_profile = self.service.update_user_profile(self.test_user.id, profile_data)
        self.assertEqual(updated_profile.bio, 'Updated bio')
        self.assertEqual(updated_profile.website, 'https://updated.com')
    
    def test_update_user_profile_non_existing(self):
        profile = self.service.update_user_profile(999, {'bio': 'Updated bio'})
        self.assertIsNone(profile)
    
    def test_update_reputation(self):
        updated_profile = self.service.update_reputation(self.test_user.id, 10)
        self.assertEqual(updated_profile.reputation, 10)
        
        updated_profile = self.service.update_reputation(self.test_user.id, 5)
        self.assertEqual(updated_profile.reputation, 15)
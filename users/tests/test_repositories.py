from django.contrib.auth.models import User
from django.test import TestCase

from users.models import UserProfile
from users.repositories import UserRepository


class UserRepositoryTest(TestCase):
    def setUp(self):
        self.repo = UserRepository()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )
        self.profile = UserProfile.objects.get(user=self.test_user)
    
    def test_create_profile(self):
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='password123'
        )
        UserProfile.objects.filter(user=user).delete()

        profile = self.repo.create_profile(user)
        self.assertIsInstance(profile, UserProfile)
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.reputation, 0)
    
    def test_get_all_users(self):
        users = self.repo.get_all_users()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.test_user)
    
    def test_get_user_by_username_existing(self):
        user = self.repo.get_user_by_username('testuser')
        self.assertEqual(user, self.test_user)
    
    def test_get_user_by_username_non_existing(self):
        user = self.repo.get_user_by_username('nonexistentuser')
        self.assertIsNone(user)
    
    def test_get_user_by_id_existing(self):
        user = self.repo.get_user_by_id(self.test_user.id)
        self.assertEqual(user, self.test_user)
    
    def test_get_user_by_id_non_existing(self):
        user = self.repo.get_user_by_id(999)
        self.assertIsNone(user)
    
    def test_create_user(self):
        user_data = {
            'username': 'newuser2',
            'email': 'new2@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        user = self.repo.create_user(user_data)
        self.assertEqual(user.username, 'newuser2')
        self.assertEqual(user.email, 'new2@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
    
    def test_authenticate_user_valid(self):
        user = self.repo.authenticate_user('testuser', 'password123')
        self.assertEqual(user, self.test_user)
    
    def test_authenticate_user_invalid_password(self):
        user = self.repo.authenticate_user('testuser', 'wrongpassword')
        self.assertIsNone(user)
    
    def test_authenticate_user_invalid_username(self):
        user = self.repo.authenticate_user('nonexistentuser', 'password123')
        self.assertIsNone(user)
    
    def test_update_user(self):
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        updated_user = self.repo.update_user(self.test_user, update_data)
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.email, 'updated@example.com')
    
    def test_get_profile_existing(self):
        profile = self.repo.get_profile(self.test_user.id)
        self.assertEqual(profile, self.profile)
    
    def test_get_profile_non_existing(self):
        profile = self.repo.get_profile(999)
        self.assertIsNone(profile)
    
    def test_update_profile(self):
        profile_data = {
            'bio': 'Updated bio',
            'website': 'https://updated.com'
        }
        updated_profile = self.repo.update_profile(self.profile, profile_data)
        self.assertEqual(updated_profile.bio, 'Updated bio')
        self.assertEqual(updated_profile.website, 'https://updated.com')
    
    def test_update_user_reputation(self):
        updated_profile = self.repo.update_user_reputation(self.test_user.id, 5)
        self.assertEqual(updated_profile.reputation, 5)
        
        # Test another update
        updated_profile = self.repo.update_user_reputation(self.test_user.id, 10)
        self.assertEqual(updated_profile.reputation, 15)
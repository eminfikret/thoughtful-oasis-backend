from django.contrib.auth.models import User
from django.test import TestCase

from users.models import UserProfile
from users.serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserDetailSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)


class SerializersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.bio = "Test bio"
        self.profile.website = "https://example.com"
        self.profile.reputation = 10
        self.profile.save()
    
    def test_user_profile_serializer(self):
        serializer = UserProfileSerializer(self.profile)
        data = serializer.data
        
        self.assertEqual(data['bio'], 'Test bio')
        self.assertEqual(data['website'], 'https://example.com')
        self.assertEqual(data['reputation'], 10)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_user_serializer(self):
        # refresh from database to ensure profile is actually loaded
        user = User.objects.get(id=self.user.id) 
        serializer = UserSerializer(user)
        data = serializer.data
        
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertIn('profile', data)
        self.assertEqual(data['profile']['bio'], 'Test bio')
        self.assertEqual(data['profile']['website'], 'https://example.com')
    
    def test_user_detail_serializer(self):
        # Refresh from database to ensure profile is fully loaded
        user = User.objects.get(id=self.user.id)
        serializer = UserDetailSerializer(user)
        data = serializer.data
        
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertIn('profile', data)
        self.assertEqual(data['profile']['bio'], 'Test bio')
        self.assertEqual(data['profile']['website'], 'https://example.com')
    
    def test_user_detail_serializer_update(self):
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'profile': {
                'bio': 'Updated bio',
                'website': 'https://updated.com'
            }
        }
        serializer = UserDetailSerializer(self.user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.profile.bio, 'Updated bio')
        self.assertEqual(updated_user.profile.website, 'https://updated.com')
    
    def test_register_serializer(self):
        data = {
            'username': 'newuser',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # password mismatch testing
        data_mismatch = data.copy()
        data_mismatch['password2'] = 'MismatchedPass123!'
        serializer = RegisterSerializer(data=data_mismatch)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_register_serializer_with_too_short_password(self):
        """Test that weak passwords are rejected"""
        data = {
            'username': 'newuser',
            'password': 'weak',  # test with too short password
            'password2': 'weak',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        # Test numeric-only password
        data['password'] = data['password2'] = '12345678'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_login_serializer(self):
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        serializer = LoginSerializer(data={'username': 'testuser'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_user_profile_update_serializer(self):
        data = {
            'bio': 'New bio content',
            'website': 'https://newsite.com'
        }
        serializer = UserProfileUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bio'], 'New bio content')
        self.assertEqual(serializer.validated_data['website'], 'https://newsite.com')
    
    def test_password_validation_variations(self):
        """Test various password patterns against Django's validation rules"""
        base_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        # password too similar to username
        data = base_data.copy()
        data['password'] = data['password2'] = 'newuser123'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        # common password from Django's list
        data = base_data.copy()
        data['password'] = data['password2'] = 'password123'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        # valid and complex password
        data = base_data.copy()
        data['password'] = data['password2'] = 'Complex8$Password!'
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), 
               f"Valid password rejected with errors: {serializer.errors if not serializer.is_valid() else 'None'}")
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile


class UserControllersTest(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

        self.profile = UserProfile.objects.get(user=self.test_user)
        self.profile.bio = "Test bio"
        self.profile.website = "https://example.com"
        self.profile.save()
        
        self.refresh = RefreshToken.for_user(self.test_user)
        self.token = str(self.refresh.access_token)
        
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # second user for testing
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123',
            first_name='Other',
            last_name='User'
        )
    
    def test_user_list_controller_get(self):
        """Test getting all users"""
        url = reverse('user-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  #  testuser and otheruser
    
    def test_register_controller_post(self):
        """Test user registration"""
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'new@example.com')
        

        user = User.objects.get(username='newuser')
        self.assertIsNotNone(user)
        self.assertIsNotNone(user.profile)  # profile should be created too
    
    def test_register_controller_post_password_mismatch(self):
        """Test user registration with mismatched passwords"""
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password2': 'DifferentPass456!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_login_controller_post_valid(self):
        """Test valid login"""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_login_controller_post_invalid(self):
        """Test invalid login"""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_user_detail_controller_get(self):
        """Test getting user details"""
        url = reverse('user-detail', args=[self.test_user.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('profile', response.data)
    
    def test_user_detail_controller_get_nonexistent(self):
        """Test getting non-existent user details"""
        url = reverse('user-detail', args=[999])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_detail_controller_put(self):
        """Test updating user details"""
        url = reverse('user-detail', args=[self.test_user.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'profile': {
                'bio': 'Updated bio',
                'website': 'https://updated.com'
            }
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['profile']['bio'], 'Updated bio')
        self.assertEqual(response.data['profile']['website'], 'https://updated.com')
    
    def test_user_detail_controller_put_unauthorized(self):
        """Test updating another user's details (should fail)"""
        url = reverse('user-detail', args=[self.other_user.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'first_name': 'Should',
            'last_name': 'Fail',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_profile_controller_get(self):
        """Test getting a user profile"""
        url = reverse('user-profile', args=[self.test_user.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], 'Test bio')
        self.assertEqual(response.data['website'], 'https://example.com')
    
    def test_user_profile_controller_patch(self):
        """Test updating a user profile"""
        url = reverse('user-profile', args=[self.test_user.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'bio': 'New bio',
            'website': 'https://newsite.com'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], 'New bio')
        self.assertEqual(response.data['website'], 'https://newsite.com')
    
    def test_user_profile_controller_patch_unauthorized(self):
        """Test updating another user's profile (should fail)"""
        url = reverse('user-profile', args=[self.other_user.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'bio': 'Should fail',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_check_username_email_controller_get_username_exists(self):
        """Test checking if an existing username exists"""
        url = reverse('check-availability')
        response = self.client.get(f"{url}?username={self.test_user.username}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['username_exists'])

        if 'email_exists' in response.data:
            self.assertFalse(response.data['email_exists'])

    def test_check_username_email_controller_get_username_not_exists(self):
        """Test checking if a non-existing username exists"""
        url = reverse('check-availability')
        response = self.client.get(f"{url}?username=nonexistentuser")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['username_exists'])

        if 'email_exists' in response.data:
            self.assertFalse(response.data['email_exists'])

    def test_check_username_email_controller_get_email_exists(self):
        """Test checking if an existing email exists"""
        url = reverse('check-availability')
        response = self.client.get(f"{url}?email={self.test_user.email}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['email_exists'])

        if 'username_exists' in response.data:
            self.assertFalse(response.data['username_exists'])

    def test_check_username_email_controller_get_email_not_exists(self):
        """Test checking if a non-existing email exists"""
        url = reverse('check-availability')
        response = self.client.get(f"{url}?email=nonexistent@example.com")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['email_exists'])

        if 'username_exists' in response.data:
            self.assertFalse(response.data['username_exists'])

    def test_check_username_email_controller_get_both(self):
        """Test checking both username and email"""
        url = reverse('check-availability')
        response = self.client.get(
            f"{url}?username={self.test_user.username}&email=nonexistent@example.com"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['username_exists'])
        self.assertFalse(response.data['email_exists'])

    def test_check_username_email_controller_get_no_params(self):
        """Test checking without any parameters"""
        url = reverse('check-availability')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_check_username_email_controller_get_case_insensitive_username(self):
        """Test that username checking is case-insensitive"""
        url = reverse('check-availability')
        upper_username = self.test_user.username.upper()
        response = self.client.get(f"{url}?username={upper_username}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['username_exists'])

    def test_check_username_email_controller_get_case_insensitive_email(self):
        """Test that email checking is case-insensitive"""
        url = reverse('check-availability')
        upper_email = self.test_user.email.upper()
        response = self.client.get(f"{url}?email={upper_email}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['email_exists'])
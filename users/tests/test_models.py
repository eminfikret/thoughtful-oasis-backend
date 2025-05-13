from django.contrib.auth.models import User
from django.test import TestCase

from users.models import UserProfile


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.bio = "Test bio"
        self.profile.website = "https://example.com"
        self.profile.save()
    
    def test_profile_creation(self):
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.bio, "Test bio")
        self.assertEqual(self.profile.website, "https://example.com")
        self.assertEqual(self.profile.reputation, 0)
    
    def test_profile_string_representation(self):
        expected_string = "testuser's profile"
        self.assertEqual(str(self.profile), expected_string)
    
    def test_profile_is_linked_to_user(self):
        user_profile = self.user.profile
        self.assertEqual(user_profile, self.profile)
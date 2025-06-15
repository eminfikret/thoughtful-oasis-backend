from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from common.test_utils import disable_fact_checking_signals
from posts.models import Post


class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test description',
            slug='test-channel',
            owner=self.user
        )

    def test_post_creation(self):
        """Test creating a post"""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            channel=self.channel
        )

        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.content, 'Test content')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.channel, self.channel)
        self.assertEqual(post.__str__(), 'Test Post')
        
    def test_post_related_fields(self):
        """Test post relationships with other models"""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            channel=self.channel
        )
        
        self.assertIn(post, self.user.posts.all())

        self.assertIn(post, self.channel.channels.all())
        
    def test_post_ordering(self):
        """Test that posts are ordered by created_at field"""
        post1 = Post.objects.create(
            title='First Post',
            content='Content 1',
            author=self.user,
            channel=self.channel
        )
        
        post2 = Post.objects.create(
            title='Second Post',
            content='Content 2',
            author=self.user,
            channel=self.channel
        )
        
        posts = Post.objects.all()
        self.assertEqual(posts[0], post1)
        self.assertEqual(posts[1], post2)
        
    def test_post_claims_xml_field(self):
        """Test the claims_xml field for storing XML representation of post with claim links"""
        with disable_fact_checking_signals():
            post = Post.objects.create(
                title='Test Post with Claims',
                content='This post contains factual claims that can be linked.',
                author=self.user,
                channel=self.channel
            )
    
        self.assertIsNone(post.claims_xml)
    
        test_xml = "<text>This post contains <link id=\"1\">factual claims</link> that " \
        "can be linked.</text>"
        post.claims_xml = test_xml
        post.save()
    
        refreshed_post = Post.objects.get(pk=post.pk)
        self.assertEqual(test_xml, refreshed_post.claims_xml)
    
        post.claims_xml = None
        post.save()
        refreshed_post = Post.objects.get(pk=post.pk)
        self.assertIsNone(refreshed_post.claims_xml)
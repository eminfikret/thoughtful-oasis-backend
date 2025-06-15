from django.contrib.auth.models import User
from django.test import TestCase

from channels.models import Channel
from common.params import PaginationParams
from common.test_utils import disable_fact_checking_signals
from posts.models import Post
from posts.repositories import PostRepository


class PostRepositoryTest(TestCase):
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
        
        with disable_fact_checking_signals():

            self.post1 = Post.objects.create(
                title='First Post',
                content='First content',
                author=self.user,
                channel=self.channel
            )
            
            self.post2 = Post.objects.create(
                title='Second Post',
                content='Second content',
                author=self.user,
                channel=self.channel
            )

    def test_create_post(self):
        """Test creating a post via repository"""
        with disable_fact_checking_signals():
            post = PostRepository.create_post(
                title='Test Post',
                content='Test content',
                channel_id=self.channel.id,
                author=self.user
            )
            
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.content, 'Test content')
        self.assertEqual(post.channel_id, self.channel.id)
        self.assertEqual(post.author, self.user)
        
    def test_get_post_by_id(self):
        """Test getting a post by ID"""
        post = PostRepository.get_post_by_id(self.post1.id)
        
        self.assertEqual(post.id, self.post1.id)
        self.assertEqual(post.title, self.post1.title)
        
    def test_get_post_by_id_not_found(self):
        """Test getting a non-existent post by ID"""
        post = PostRepository.get_post_by_id(999)
        
        self.assertIsNone(post)
    
    def test_get_all_posts(self):
        """Test getting all posts"""
        pagination = PaginationParams(limit=10, offset=0)
        posts = PostRepository.get_all_posts(pagination=pagination)
        
        self.assertEqual(len(posts), 2)
        self.assertIn(self.post1, posts)
        self.assertIn(self.post2, posts)
        
    def test_get_all_posts_with_pagination(self):
        """Test pagination of posts"""
        with disable_fact_checking_signals():
            Post.objects.create(
                title='Third Post',
                content='Third content',
                author=self.user,
                channel=self.channel
            )

        pagination = PaginationParams(limit=2, offset=0)
        posts = PostRepository.get_all_posts(pagination=pagination)
        self.assertEqual(len(posts), 2)

        pagination = PaginationParams(limit=2, offset=2)
        posts = PostRepository.get_all_posts(pagination=pagination)
        self.assertEqual(len(posts), 1)
        
        pagination = PaginationParams(limit=2, offset=1)
        posts = PostRepository.get_all_posts(pagination=pagination)
        self.assertEqual(len(posts), 2)
        post_ids = [post.id for post in posts]
        self.assertIn(self.post2.id, post_ids)
        
    def test_get_all_posts_with_search(self):
        """Test searching posts"""
        pagination = PaginationParams(limit=10, offset=0)
        posts = PostRepository.get_all_posts(search='First', pagination=pagination)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, self.post1.id)
        
    def test_get_all_posts_with_channel(self):
        """Test filtering posts by channel"""
        channel2 = Channel.objects.create(
            name='Second Channel',
            description='Another channel',
            slug='channel-2',
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            post3 = Post.objects.create(
                title='Channel 2 Post',
                content='Content in channel 2',
                author=self.user,
                channel=channel2
            )
            
        pagination = PaginationParams(limit=10, offset=0)

        posts = PostRepository.get_all_posts(pagination=pagination, channel=self.channel)
        self.assertEqual(len(posts), 2)
        self.assertNotIn(post3, posts)

        posts = PostRepository.get_all_posts(pagination=pagination, channel=channel2)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, post3.id)
        
    def test_update_post(self):
        """Test updating a post"""
        updated_post = PostRepository.update_post(
            post_id=self.post1.id,
            title='Updated Title',
            content='Updated content'
        )
        
        self.assertEqual(updated_post.title, 'Updated Title')
        self.assertEqual(updated_post.content, 'Updated content')

        refreshed_post = Post.objects.get(id=self.post1.id)
        self.assertEqual(refreshed_post.title, 'Updated Title')
        self.assertEqual(refreshed_post.content, 'Updated content')
        
    def test_delete_post(self):
        """Test deleting a post"""
        PostRepository.delete_post(self.post1.id)

        self.assertEqual(Post.objects.count(), 1)
        self.assertFalse(Post.objects.filter(id=self.post1.id).exists())

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from channels.exceptions import ChannelNotFoundException
from channels.models import Channel
from common.params import PaginationParams
from common.test_utils import MockLLMTestMixin, disable_fact_checking_signals
from posts.dtos import CreatePostDto, UpdatePostDto
from posts.exceptions import PostNotFoundException, UnauthorizedPostAccessException
from posts.models import Post
from posts.services import PostService
from posts.types import PostId


class PostServiceTest(MockLLMTestMixin, TestCase):
    def setUp(self):
        super().setUp() 
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpassword'
        )
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test description',
            slug='test-channel',
            owner=self.user
        )
        
        with disable_fact_checking_signals():
            self.post = Post.objects.create(
                title='Test Post',
                content='Test content',
                author=self.user,
                channel=self.channel
            )

    def test_create_post(self):
        """Test creating a post via service"""
        with disable_fact_checking_signals():
            post = PostService.create_post(
                CreatePostDto(
                    channel_id=self.channel.id,
                    title='New Post',
                    content='New content'
                ),
                author=self.user
            )
            
        self.assertEqual(post.title, 'New Post')
        self.assertEqual(post.content, 'New content')
        self.assertEqual(post.channel_id, self.channel.id)
        self.assertEqual(post.author, self.user)
        
    def test_create_post_invalid_channel(self):
        """Test creating a post with invalid channel ID"""
        with patch('channels.services.ChannelService.get_channel_by_id', return_value=None):
            with self.assertRaises(ChannelNotFoundException):
                PostService.create_post(
                    CreatePostDto(
                        channel_id=999,  
                        title='New Post',
                        content='New content'
                    ),
                    author=self.user
                )
            
    def test_get_post_by_id(self):
        """Test getting a post by ID"""
        post = PostService.get_post_by_id(PostId(self.post.id))
        
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.title, self.post.title)
        
    def test_get_post_by_id_not_found(self):
        """Test getting a non-existent post by ID"""
        with self.assertRaises(PostNotFoundException):
            PostService.get_post_by_id(PostId(999))
            
    def test_get_all_posts(self):
        """Test getting all posts"""
        pagination = PaginationParams(limit=10, offset=0)
        posts = PostService.get_all_posts(pagination)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, self.post.id)
        
    def test_get_posts_by_channel(self):
        """Test getting posts by channel"""
        pagination = PaginationParams(limit=10, offset=0)
        posts = PostService.get_posts_by_channel(
            channel_id=self.channel.id,
            requester=self.user,
            pagination=pagination
        )
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, self.post.id)
        
    def test_update_post_success(self):
        """Test updating a post by owner"""
        with disable_fact_checking_signals():
            updated_post = PostService.update_post(
                PostId(self.post.id),
                UpdatePostDto(
                    title='Updated Title',
                    content='Updated content'
                ),
                user=self.user
            )
            
        self.assertEqual(updated_post.title, 'Updated Title')
        self.assertEqual(updated_post.content, 'Updated content')
        
    def test_update_post_unauthorized(self):
        """Test updating a post by non-owner"""
        with self.assertRaises(UnauthorizedPostAccessException):
            PostService.update_post(
                PostId(self.post.id),
                UpdatePostDto(
                    title='Updated Title',
                    content='Updated content'
                ),
                user=self.other_user
            )
            
    def test_update_post_not_found(self):
        """Test updating a non-existent post"""
        with self.assertRaises(PostNotFoundException):
            PostService.update_post(
                PostId(999),
                UpdatePostDto(
                    title='Updated Title',
                    content='Updated content'
                ),
                user=self.user
            )
            
    def test_delete_post_success(self):
        """Test deleting a post by owner"""
        PostService.delete_post(PostId(self.post.id), self.user)

        self.assertEqual(Post.objects.count(), 0)
        
    def test_delete_post_unauthorized(self):
        """Test deleting a post by non-owner"""
        with self.assertRaises(UnauthorizedPostAccessException):
            PostService.delete_post(PostId(self.post.id), self.other_user)

        self.assertEqual(Post.objects.count(), 1)
        
    def test_delete_post_not_found(self):
        """Test deleting a non-existent post"""
        with self.assertRaises(PostNotFoundException):
            PostService.delete_post(PostId(999), self.user)
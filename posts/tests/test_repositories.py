from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post
from posts.repositories import PostRepository

User = get_user_model()

class PostRepositoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='repo_user', password='password')
        self.channel_id = 1

    def test_create_post_creates_and_returns_post(self):
        title = 'Repo Post'
        content = 'Repo Content'
        post = PostRepository.create_post(
            title=title,
            content=content,
            channel_id=self.channel_id,
            author=self.user
        )
        self.assertIsInstance(post, Post)
        self.assertEqual(post.title, title)
        self.assertEqual(post.content, content)
        self.assertEqual(post.channel_id, self.channel_id)
        self.assertEqual(post.author, self.user)
        self.assertTrue(Post.objects.filter(id=post.id).exists())

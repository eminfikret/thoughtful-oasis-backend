from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from channels.models import Channel
from comments.models import Comment  # assuming app is called `comments`
from posts.models import Post  # assuming your app is called `posts`


class CommentControllerTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.channel = Channel.objects.create(
            name='Test Channel',
            description='Test Desc',
            slug='test-channel',
            owner=self.user
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Post content',
            channel=self.channel,
            author=self.user
        )

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_create_comment_success(self):
        self.authenticate(self.user)
        url = reverse('comments-create')
        data = {
            "post_id": self.post.id,
            "content": "This is a top-level comment"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().content, "This is a top-level comment")

    def test_create_comment_requires_auth(self):
        url = reverse('comments-create')
        data = {"post_id": self.post.id, "content": "Unauthorized comment"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reply_to_comment(self):
        self.authenticate(self.user)
        parent = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="Original comment"
        )
        url = reverse('comments-reply')
        data = {
            "parent_comment_id": parent.id,
            "content": "This is a reply"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)
        reply = Comment.objects.get(parent_comment=parent)
        self.assertEqual(reply.content, "This is a reply")

    def test_get_replies(self):
        self.authenticate(self.user)
        parent = Comment.objects.create(post=self.post, author=self.user,
                                         content="Parent comment")
        Comment.objects.create(post=self.post, author=self.user, content="Reply 1",
                                parent_comment=parent)
        Comment.objects.create(post=self.post, author=self.user, content="Reply 2",
                                parent_comment=parent)

        url = reverse('comments-replies', kwargs={"comment_id": parent.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["content"], "Reply 1")
# from unittest import TestCase
# from unittest.mock import MagicMock, patch

# from django.contrib.auth import get_user_model

# from posts.dtos import CreatePostDto
# from posts.services import PostService

# User = get_user_model()

# class PostServiceTest(TestCase):
#     @patch('posts.repositories.PostRepository.create_post')
#     def test_create_post_calls_repository(self, mock_create_post):
#         dto = CreatePostDto(title='Test Title', content='Test Content', channel_id=1)
#         user = MagicMock(spec=User)
#         mock_post = MagicMock()
#         mock_create_post.return_value = mock_post

#         result = PostService.create_post(dto, author=user)

#         mock_create_post.assert_called_once_with(
#             title=dto.title,
#             content=dto.content,
#             channel_id=dto.channel_id,
#             author=user
#         )
#         self.assertEqual(result, mock_post)

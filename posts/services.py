from typing import List, Optional

from django.contrib.auth.models import User

from channels.exceptions import (
    ChannelNotFoundException,
)
from channels.services import ChannelService
from channels.types import ChannelId
from common.params import PaginationParams
from posts.dtos import CreatePostDto, UpdatePostDto
from posts.exceptions import PostNotFoundException, UnauthorizedPostAccessException
from posts.models import Post
from posts.repositories import PostRepository
from posts.types import PostId


class PostService:
    @staticmethod
    def get_all_posts(params: PaginationParams) -> List[Post]:
        return PostRepository.get_all_posts(params)

    @staticmethod
    def get_posts_by_channel(
            channel_id: int,
            requester: User,
            search: Optional[str] = None,
            pagination: Optional[PaginationParams] = None
    ) -> List[Post]:
        """
        Returns posts for a given channel with optional pagination.
        Raises:
            ChannelNotFoundException: if no channel exists with the given ID.
            PermissionDenied: if requester isn't allowed (optional).
        """
        pagination = pagination or PaginationParams()

        channel = ChannelService.get_channel_by_id(channel_id)
        if not channel:
            raise ChannelNotFoundException()


        return PostRepository.get_all_posts(channel=channel, pagination=pagination)

    @staticmethod
    def get_posts_count_by_channel(
            channel_id: ChannelId,
            search: Optional[str] = None,
    ) -> int:
        channel = ChannelService.get_channel_by_id(channel_id)


        return PostRepository.get_posts_count_by_channel(channel=channel, search=search)

    @staticmethod
    def get_posts_count(search: Optional[str] = None) -> int:
        return PostRepository.get_posts_count(search)

    @staticmethod
    def get_post_by_id(post_id: PostId) -> Post:
        """
        Raises:
            PostNotFoundException: if no post exists with the given ID.
        """
        post = PostRepository.get_post_by_id(post_id)
        if post is None:
            raise PostNotFoundException(post_id)
        return post

    @staticmethod
    def create_post(dto: CreatePostDto, author: User) -> Post:
        """
        Creates a new post in the given channel by the given author.
        """
        return PostRepository.create_post(
            title=dto.title,
            content=dto.content,
            channel_id=dto.channel_id,
            author=author
        )

    @staticmethod
    def update_post(post_id: PostId, dto: UpdatePostDto, user: User) -> Post:
        """
        Raises:
            PostNotFoundException: if no post exists with the given ID.
            UnauthorizedPostAccessException: if the user is not the post's author nor staff.
        """
        has_changes = False

        post = PostService.get_post_by_id(post_id)

        if not (post.author == user or user.is_staff):
            raise UnauthorizedPostAccessException(post_id)

        if dto.title is not None:
            post.title = dto.title
        if dto.content is not None:
            post.content = dto.content


        if has_changes:
            return PostRepository.update_post(post)

        return post

    @staticmethod
    def delete_post(post_id: PostId, user: User) -> None:
        """
        Raises:
            PostNotFoundException: if no post exists with the given ID.
            UnauthorizedPostAccessException: if the user is not the post's author nor staff.
        """
        post = PostService.get_post_by_id(post_id)

        if not (post.author == user or user.is_staff):
            raise UnauthorizedPostAccessException(post_id)

        PostRepository.delete_post(post)
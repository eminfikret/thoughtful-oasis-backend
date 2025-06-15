from typing import List, Optional

from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

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
    def get_all_posts(pagination: PaginationParams, search: Optional[str] = None) -> List[Post]:
        return PostRepository.get_all_posts(search=search, pagination=pagination)

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
            PermissionDenied: if requester isn't allowed
        """
        pagination = pagination or PaginationParams()

        channel = ChannelService.get_channel_by_id(channel_id)
        if not channel:
            raise ChannelNotFoundException()

        return PostRepository.get_all_posts(channel=channel, pagination=pagination, search=search)

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
        channel = ChannelService.get_channel_by_id(dto.channel_id)
        if not channel:
            raise ChannelNotFoundException(f"Channel with ID {dto.channel_id} not found")
            
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
        post = PostService.get_post_by_id(post_id)

        if not (post.author == user or user.is_staff):
            raise UnauthorizedPostAccessException(post_id)

        if dto.title is not None:
            post.title = dto.title
        if dto.content is not None:
            post.content = dto.content

        post.claims_xml = None
        post.save(update_fields=['title', 'content', 'claims_xml'])
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

        PostRepository.delete_post(post.id)

    @staticmethod
    def get_user_posts(user_id: int, offset: int = 0, limit: int = 10):
        """Get posts created by a specific user with pagination"""
        get_object_or_404(User, id=user_id)
        posts = PostRepository.get_posts_by_user(user_id, offset, limit)
        total = PostRepository.count_user_posts(user_id)
        return posts, total

    @staticmethod
    def get_top_posts(offset=0, limit=10, days=5):
        """
        Get posts sorted by vote score (highest first) within a specified time window
        (default 5 days).
        
        Args:
            offset: Pagination offset
            limit: Number of posts to return
            days: Number of days to look back
        """
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        posts = Post.objects.filter(created_at__gte=cutoff_date).annotate(
            score=Count('votes', filter=Q(votes__is_upvote=True)) - 
                  Count('votes', filter=Q(votes__is_upvote=False))
        ).order_by('-score')
        
        total = posts.count()
        posts = posts[offset:offset+limit]
        
        return posts, total

from typing import List, Optional

from django.db.models import Q

from common.params import PaginationParams
from posts.models import Channel, Post
from posts.types import PostId


class PostRepository:
    @staticmethod
    def get_all_posts(
            search: Optional[str] = None,
            pagination: Optional[PaginationParams] = None,
            channel: Optional[Channel] = None,
    ) -> List[Post]:
        pagination = pagination or PaginationParams()
        queryset = Post.objects.select_related('channel', 'author').all().order_by('-id')

        if channel is not None:
            queryset = queryset.filter(channel=channel)

        if search is not None:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search)
            )

        return list(queryset[pagination.offset:pagination.offset + pagination.limit])

    @staticmethod
    def get_posts_count(search: Optional[str] = None) -> int:
        """
        Returns total count of Post records.
        Optional filtering by search term.
        """
        queryset = Post.objects.all()

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        return queryset.count()

    @staticmethod
    def get_post_by_id(post_id: PostId) -> Optional[Post]:
        """
        Returns the Post with the given ID, or None if not found.
        """
        try:
            return Post.objects.select_related('author', 'channel').get(pk=post_id)
        except Post.DoesNotExist:
            return None

    @staticmethod
    def get_posts_count_by_channel(
            channel: Channel,
            search: Optional[str] = None
    ) -> int:
        queryset = Post.objects.filter(channel=channel)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        return queryset.count()

    @staticmethod
    def create_post(
            title: str,
            content: str,
            channel_id: int,
            author,
    ) -> Post:
        """
        Creates and returns a new Post.
        """
        return Post.objects.create(
            title=title,
            content=content,
            channel_id=channel_id,
            author=author
        )

    @staticmethod
    def update_post(post_id: int, title: str = None, content: str = None) -> Post:
        """
        Updates a post with the given ID.
        """
        if isinstance(post_id, Post):
            post = post_id
        else:
            post = Post.objects.get(id=post_id)
    
        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        
        post.save()
        return post
    
    @staticmethod
    def delete_post(post_id: int) -> None:
        """
        Deletes a post with the given ID.
        """
        if isinstance(post_id, Post):
            post = post_id 
        else:
            post = Post.objects.get(id=post_id)
    
        post.delete()

    @staticmethod
    def get_posts_by_user(user_id, offset=0, limit=10):
        """Get all posts created by a specific user with pagination"""
        return Post.objects.filter(
            author_id=user_id
        ).select_related(
            'author', 'channel'
        ).order_by(
            '-created_at'
        )[offset:offset+limit]

    @staticmethod
    def count_user_posts(user_id):
        """Count total posts made by a specific user"""
        return Post.objects.filter(author_id=user_id).count()

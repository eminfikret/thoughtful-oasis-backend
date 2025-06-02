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
        import logging
        logging.info(f"get_all_posts called with search='{search}'")
        
        pagination = pagination or PaginationParams()
        queryset = Post.objects.select_related('channel', 'author').all()

        if channel:
            queryset = queryset.filter(channel=channel)

        all_posts = list(Post.objects.all())
        logging.info(f"Total posts in database: {len(all_posts)}")
        for post in all_posts:
            logging.info(
                f"Available post: {post.id} - Title: {post.title}, "
                f"Content: {post.content}"
            )

        if search is not None:
            search = search.strip()
            if search:  
                logging.info(f"Filtering posts for search term: '{search}'")

                filtered_posts = []
                for post in list(queryset):
                    title_match = search.lower() in post.title.lower()
                    content_match = search.lower() in post.content.lower()
                    if title_match or content_match:
                        filtered_posts.append(post)
                        logging.info(f"Match found: {post.id} - {post.title}")
                    else:
                        logging.info(f"No match: {post.id} - {post.title}")
                
                logging.info(f"Found {len(filtered_posts)} posts matching '{search}'")

                result = filtered_posts[pagination.offset:pagination.offset + pagination.limit]
                return result

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
    def update_post(post: Post) -> Post:
        """
        Persists changes to an existing Post instance.
        """
        post.save(update_fields=[
            field for field in ['title', 'content', 'updated_at']
            if field in post.get_dirty_fields()
        ])
        return post

    @staticmethod
    def delete_post(post: Post) -> None:
        """
        Deletes the given Post instance.
        """
        post.delete()

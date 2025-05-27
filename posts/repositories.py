from typing import Optional, List

from django.db.models import QuerySet

from posts.models import Post
from posts.params import PostsParams
from posts.types import PostId


class PostRepository:
    @staticmethod
    def get_all_posts(params: PostsParams) -> List[Post]:
        """
        Returns a paginated, ordered list of Posts.
        """
        qs: QuerySet = Post.objects.select_related('author', 'channel').all()

        # Apply ordering if provided
        if params.ordering:
            qs = qs.order_by(params.ordering)

        # Pagination
        if params.page is not None and params.page_size is not None:
            offset = (params.page - 1) * params.page_size
            limit = offset + params.page_size
            qs = qs[offset:limit]

        return list(qs)

    @staticmethod
    def get_posts_count() -> int:
        """
        Returns total count of Post records.
        """
        return Post.objects.count()

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
            if field in post.get_dirty_fields()  # or simply save all
        ])
        return post

    @staticmethod
    def delete_post(post: Post) -> None:
        """
        Deletes the given Post instance.
        """
        post.delete()

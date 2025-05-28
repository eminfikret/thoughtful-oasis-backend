from django.db.models.signals import post_save
from contextlib import contextmanager

from claims.signals import process_post_fact_checking, process_comment_fact_checking


@contextmanager
def disable_fact_checking_signals():
    post_save.disconnect(process_post_fact_checking, sender='posts.Post')
    post_save.disconnect(process_comment_fact_checking, sender='comments.Comment')
    
    try:
        yield
    finally:
        from posts.models import Post
        from comments.models import Comment
        post_save.connect(process_post_fact_checking, sender=Post)
        post_save.connect(process_comment_fact_checking, sender=Comment)
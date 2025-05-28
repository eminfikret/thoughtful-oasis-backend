from contextlib import contextmanager

from django.db.models.signals import post_save

from claims.signals import process_comment_fact_checking, process_post_fact_checking


@contextmanager
def disable_fact_checking_signals():
    post_save.disconnect(process_post_fact_checking, sender='posts.Post')
    post_save.disconnect(process_comment_fact_checking, sender='comments.Comment')
    
    try:
        yield
    finally:
        from comments.models import Comment
        from posts.models import Post
        post_save.connect(process_post_fact_checking, sender=Post)
        post_save.connect(process_comment_fact_checking, sender=Comment)
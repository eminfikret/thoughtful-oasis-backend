from django.apps import apps
from django.db.models.signals import post_save

from claims.signals import process_comment_fact_checking, process_post_fact_checking

post_save.disconnect(process_comment_fact_checking, sender=apps.get_model('comments', 'Comment'))
post_save.disconnect(process_post_fact_checking, sender=apps.get_model('posts', 'Post'))
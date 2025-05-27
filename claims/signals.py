from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from posts.models import Post
from comments.models import Comment
from .models import Claim
from .services import ClaimService

claim_service = ClaimService()

@receiver(post_save, sender=Post)
def process_post_fact_checking(sender, instance, created, **kwargs):
    """
    Process fact checking when a post is created or updated
    
    Args:
        sender: The model class
        instance: The actual post instance
        created: Boolean indicating if this is a new instance
    """

    if not instance.content:
        return

    if not created:
        with transaction.atomic():
            claims = Claim.objects.filter(post_id=instance.id)
            claims.delete()

    claim_service.process_content_for_claims(
        user_id=instance.author_id, 
        content=instance.content,
        source_type='post',
        source_id=instance.id
    )


@receiver(post_save, sender=Comment)
def process_comment_fact_checking(sender, instance, created, **kwargs):
    """
    Process fact checking when a comment is created
    
    Args:
        sender: The model class
        instance: The actual comment instance
        created: Boolean indicating if this is a new instance
    """
    if not instance.content or not created:
        return

    claim_service.process_content_for_claims(
        user_id=instance.author_id,
        content=instance.content,
        source_type='comment',
        source_id=instance.id
    )
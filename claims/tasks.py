from celery import shared_task
from django.db import transaction

from .models import Claim
from .services import ClaimService

claim_service = ClaimService()

@shared_task
def process_post_fact_checking_task(post_id, user_id, content, is_update=False):
    """
    Process post for fact checking in background
    """

    if is_update:
        with transaction.atomic():
            Claim.objects.filter(post_id=post_id).delete()

    claim_service.process_content_for_claims(
        user_id=user_id,
        content=content,
        source_type='post',
        source_id=post_id
    )


@shared_task
def process_comment_fact_checking_task(comment_id, user_id, content):
    """
    Process comment for fact checking in background
    """
    claim_service.process_content_for_claims(
        user_id=user_id,
        content=content,
        source_type='comment',
        source_id=comment_id
    )
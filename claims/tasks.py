from celery import shared_task
from django.db import transaction

from .models import Claim
from .services import ClaimService
from .utils import extract_claims_sync

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


@shared_task
def process_claim_extraction(content, source_type, source_id, user_id=None):
    """Process content for claim extraction"""
    return extract_claims_sync(content, source_type, source_id, user_id)

@shared_task
def process_post_claim_extraction(title, content, post_id):
    """Process post content for claim extraction"""
    combined_content = f"TITLE: {title}\n\n{content}"
    return process_claim_extraction(combined_content, "post", post_id)

@shared_task
def process_comment_claim_extraction(content, comment_id, user_id=None):
    """Process comment content for claim extraction"""
    return process_claim_extraction(content, "comment", comment_id, user_id)
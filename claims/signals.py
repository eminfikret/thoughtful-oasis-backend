from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from comments.models import Comment
from posts.models import Post

from .models import Claim
from .services import ClaimService

claim_service = ClaimService()

@receiver(post_save, sender=Post)
def process_post_fact_checking(sender, instance, created, **kwargs):
    if not instance.content:
        return

    if not created:
        with transaction.atomic():
            claims = Claim.objects.filter(post_id=instance.id)
            claims.delete()

    combined_text = f"TITLE: {instance.title}\n\nCONTENT:\n{instance.content}"

    claim_service.process_content_for_claims(
        user_id=instance.author_id, 
        content=combined_text,
        source_type='post',
        source_id=instance.id
    )


@receiver(post_save, sender=Comment)
def process_comment_fact_checking(sender, instance, created, **kwargs):
    """Process fact checking for a comment"""
    if not instance.content:
        return
        
    if not created:
        with transaction.atomic():
            claims = Claim.objects.filter(comment_id=instance.id)
            claims.delete()

    context = build_comment_context(instance)
    
    claim_service.process_content_for_claims(
        user_id=instance.author_id,
        content=instance.content,
        source_type='comment',
        source_id=instance.id,
        context=context 
    )

def build_comment_context(comment):
    """Build context information for a comment to aid in fact checking"""
    post = comment.post
    context = {
        "post": {
            "title": post.title,
            "content": post.content
        },
        "conversation_thread": []
    }
    
    thread = []
    current = comment.parent_comment
    depth = 0
    
    while current:
        thread.append({
            "content": current.content,
            "author": current.author.username,
            "depth": depth  
        })
        current = current.parent_comment
        depth += 1
    
    context["conversation_thread"] = list(reversed(thread))
    
    return context
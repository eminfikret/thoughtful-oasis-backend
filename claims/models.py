from django.db import models
from django.contrib.auth.models import User
from common.models import BaseModel
from rest_framework import serializers


class Claim(BaseModel):
    """Model for representing a factual claim extracted from text"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="claims", null=True)
    
    post_id = models.IntegerField(null=True, blank=True)
    comment_id = models.IntegerField(null=True, blank=True)
    
    extracted_claim = models.TextField()
    claim_index = models.IntegerField()
    
    SOURCE_TYPES = (
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('raw', 'Raw Text'),
    )
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPES)
    source_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claims'
        indexes = [
            models.Index(fields=['post_id']),
            models.Index(fields=['comment_id']),
        ]
        verbose_name = 'Claim'
        verbose_name_plural = 'Claims'
    
    def __str__(self):
        source = "Unknown"
        if self.source_type == 'post' and self.post_id:
            source = f"Post #{self.post_id}"
        elif self.source_type == 'comment' and self.comment_id:
            source = f"Comment #{self.comment_id}"
        elif self.source_type == 'raw':
            source = "Raw text"
        
        return f"{source}: {self.extracted_claim[:50]}..."


class FactCheck(BaseModel):
    """Model for storing fact check results for a claim"""
    claim = models.OneToOneField(Claim, on_delete=models.CASCADE, related_name="fact_check")
    
    VERDICT_CHOICES = (
        ('supported', 'Supported'),
        ('contradicted', 'Contradicted'),
        ('not_found', 'Not Found'),
    )
    verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fact_checks'
        verbose_name = 'Fact Check'
        verbose_name_plural = 'Fact Checks'
    
    def __str__(self):
        return f"Fact check for claim #{self.claim.id}: {self.verdict}"


class FactCheckSource(BaseModel):
    """Model for storing sources used in fact checking"""
    fact_check = models.ForeignKey(FactCheck, on_delete=models.CASCADE, related_name="sources")
    url = models.URLField()
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'fact_check_sources'
        verbose_name = 'Fact Check Source'
        verbose_name_plural = 'Fact Check Sources'
    
    def __str__(self):
        return f"Source for fact check #{self.fact_check.id}: {self.title or self.url}"
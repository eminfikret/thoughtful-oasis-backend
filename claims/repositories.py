from typing import List, Dict, Optional, Any, Union
from django.db import transaction
from django.db.utils import ProgrammingError
from django.core.exceptions import FieldError

from .models import Claim, FactCheck, FactCheckSource


class ClaimRepository:
    """Repository for interacting with claims data"""
    
    def create_claim(self, user_id: Optional[int] = None, source_type: str = "", 
                   extracted_claim: str = "", claim_index: int = 1,
                   source_text: Optional[str] = None, post_id: Optional[int] = None, 
                   comment_id: Optional[int] = None) -> Claim:
        """Create a new claim"""
        claim_data = {
            'post_id': post_id,
            'comment_id': comment_id,
            'extracted_claim': extracted_claim,
            'claim_index': claim_index,
            'source_type': source_type,
            'source_text': source_text if source_type == 'raw' else None
        }
        
        if user_id is not None:
            claim_data['user_id'] = user_id
            
        return Claim.objects.create(**claim_data)
    
    def get_claim_by_id(self, claim_id: int) -> Optional[Claim]:
        """Get a claim by its ID"""
        try:
            return Claim.objects.get(id=claim_id)
        except Claim.DoesNotExist:
            return None
        except (FieldError, ProgrammingError):
            raise FieldError("Database schema mismatch. Run migrations to update the database.")
    
    def get_claims_for_post(self, post_id: int) -> List[Claim]:
        """Get all claims for a specific post"""
        return Claim.objects.filter(post_id=post_id)
    
    def get_claims_for_comment(self, comment_id: int) -> List[Claim]:
        """Get all claims for a specific comment"""
        return Claim.objects.filter(comment_id=comment_id)
    
    def get_claims_for_user(self, user_id: int) -> List[Claim]:
        """Get all claims submitted by a user"""
        return Claim.objects.filter(user_id=user_id)
    
    def bulk_create_claims(self, claims_data: List[Dict[str, Any]]) -> List[Claim]:
        """Create multiple claims at once"""
        claims = [Claim(**data) for data in claims_data]
        return Claim.objects.bulk_create(claims)

class FactCheckRepository:
    """Repository for interacting with fact check data"""
    
    def create_fact_check(self, claim_id: int, verdict: str, summary: str) -> FactCheck:
        """Create a new fact check for a claim"""
        fact_check_data = {
            'claim_id': claim_id,
            'verdict': verdict,
            'summary': summary
        }
        return FactCheck.objects.create(**fact_check_data)
    
    def create_fact_check_with_sources(self, fact_check_data, sources_data):
        """Create a fact check with its sources in a transaction"""
        with transaction.atomic():
            fact_check = FactCheck.objects.create(**fact_check_data)
            
            if sources_data:
                sources = []
                for source_data in sources_data:
                    source_data['fact_check'] = fact_check
                    sources.append(FactCheckSource(**source_data))
                
                FactCheckSource.objects.bulk_create(sources)
            
            return fact_check
    
    def get_fact_check_by_id(self, fact_check_id: int) -> Optional[FactCheck]:
        """Get a fact check by its ID"""
        try:
            return FactCheck.objects.get(id=fact_check_id)
        except FactCheck.DoesNotExist:
            return None
    
    def get_fact_checks_for_claim(self, claim_id: int) -> List[FactCheck]:
        """Get all fact checks for a claim"""
        return FactCheck.objects.filter(claim_id=claim_id)
    
    def get_fact_check_by_claim_id(self, claim_id: int) -> Optional[FactCheck]:
        """Get a fact check by claim ID"""
        try:
            return FactCheck.objects.get(claim_id=claim_id)
        except FactCheck.DoesNotExist:
            return None
    
    def create_fact_check_source(self, fact_check_id: int, url: str, title: Optional[str] = None,
                               description: Optional[str] = None, 
                               relevance_score: Optional[float] = None) -> FactCheckSource:
        """Create a new source for a fact check"""
        source_data = {
            'fact_check_id': fact_check_id,
            'url': url,
            'title': title,
            'description': description,
            'relevance_score': relevance_score
        }
        return FactCheckSource.objects.create(**source_data)
    
    def bulk_create_fact_check_sources(self, sources_data: List[Dict[str, Any]]) -> List[FactCheckSource]:
        """Create multiple fact check sources at once"""
        sources = [FactCheckSource(**data) for data in sources_data]
        return FactCheckSource.objects.bulk_create(sources)
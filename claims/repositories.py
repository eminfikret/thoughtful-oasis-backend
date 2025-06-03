from typing import List, Optional

from django.core.exceptions import FieldError
from django.db.utils import ProgrammingError

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

    
    def get_claims_for_user(self, user_id: int) -> List[Claim]:
        """Get all claims submitted by a user"""
        return Claim.objects.filter(user_id=user_id)
    
    
    def delete_claim(self, claim_id: int) -> bool:
        """Delete a claim by ID"""
        try:
            claim = Claim.objects.get(id=claim_id)
            claim.delete()
            return True
        except Claim.DoesNotExist:
            return False

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
    
from django.db import transaction

from .models import FactualClaim, FactCheck, FactCheckSource


class ClaimRepository:
    """Repository for interacting with factual claims data"""
    
    def create_factual_claim(self, claim_data):
        """Create a new factual claim"""
        return FactualClaim.objects.create(**claim_data)
    
    def get_claim_by_id(self, claim_id):
        """Get a claim by its ID"""
        try:
            return FactualClaim.objects.get(id=claim_id)
        except FactualClaim.DoesNotExist:
            return None
    
    def get_claims_for_post(self, post_id):
        """Get all claims for a specific post"""
        return FactualClaim.objects.filter(post_id=post_id)
    
    def get_claims_for_comment(self, comment_id):
        """Get all claims for a specific comment"""
        return FactualClaim.objects.filter(comment_id=comment_id)


class FactCheckRepository:
    """Repository for interacting with fact check data"""
    
    def create_fact_check(self, fact_check_data):
        """Create a new fact check"""
        return FactCheck.objects.create(**fact_check_data)
    
    def create_fact_check_with_sources(self, fact_check_data, sources_data):
        """Create a fact check with its sources in a transaction"""
        with transaction.atomic():
            fact_check = FactCheck.objects.create(**fact_check_data)
            
            # Add sources if any
            if sources_data:
                sources = []
                for source_data in sources_data:
                    source_data['fact_check'] = fact_check
                    sources.append(FactCheckSource(**source_data))
                
                FactCheckSource.objects.bulk_create(sources)
            
            return fact_check
    
    def get_fact_check_by_id(self, fact_check_id):
        """Get a fact check by its ID"""
        try:
            return FactCheck.objects.get(id=fact_check_id)
        except FactCheck.DoesNotExist:
            return None
    
    def get_fact_checks_for_claim(self, claim_id):
        """Get all fact checks for a claim"""
        return FactCheck.objects.filter(claim_id=claim_id)
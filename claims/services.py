from django.db import transaction

from .repositories import ClaimRepository, FactCheckRepository


class ClaimService:
    """Service for handling claims"""
    
    def __init__(self):
        self.claim_repository = ClaimRepository()
        self.fact_check_repository = FactCheckRepository()
    
    def create_claim_from_post(self, post_id, content_fragment, content_position):
        """Create a claim from a post"""
        claim_data = {
            'post_id': post_id,
            'comment_id': None,  
            'content_fragment': content_fragment,
            'content_position': content_position
        }
        return self.claim_repository.create_claim(claim_data)
    
    def create_claim_from_comment(self, comment_id, content_fragment, content_position):
        """Create a claim from a comment"""
        claim_data = {
            'post_id': None,     
            'comment_id': comment_id,
            'content_fragment': content_fragment,
            'content_position': content_position
        }
        return self.claim_repository.create_claim(claim_data)
    
    def process_content_for_claims(self, content, source_type, source_id):
        """
        Process content to extract and store claims
        
        This is a placeholder for the actual claim extraction logic that will be
        implemented in another task. For now, it just creates a dummy claim.
        
        Args:
            content (str): The text content to process
            source_type (str): Either 'post' or 'comment'
            source_id (int): ID of the post or comment
            
        Returns:
            list: List of created Claim objects
        """
        # This is where a more sophisticated claim extraction would happen
        # For now, just extract the first 100 chars as a dummy claim
        if not content or len(content) < 10:
            return []
        
        # Simple example - in reality you'd use NLP to extract actual claims
        content_fragment = content[:100] if len(content) > 100 else content
        content_position = {"start": 0, "end": len(content_fragment)}
        
        if source_type == 'post':
            claim = self.create_claim_from_post(source_id, content_fragment, content_position)
        elif source_type == 'comment':
            claim = self.create_claim_from_comment(source_id, content_fragment, content_position)
        else:
            raise ValueError(f"Invalid source_type: {source_type}. Must be 'post' or 'comment'")
            
        # In a complete implementation, you'd send this claim for asynchronous processing
        # For example: queue_fact_check_task(claim.id)
        
        return [claim]


class FactCheckService:
    """Service for handling fact checking"""
    
    def __init__(self):
        self.fact_check_repository = FactCheckRepository()
    
    def create_fact_check(self, claim_id, verdict, summary=None, sources=None):
        """
        Create a fact check with sources
        
        Args:
            claim_id (int): ID of the claim to fact check
            verdict (str): The verdict ('supported', 'contradicted', 'unrelated')
            summary (str, optional): A summary of the fact check
            sources (list, optional): List of source dictionaries
            
        Returns:
            FactCheck: The created fact check object
        """
        fact_check_data = {
            'claim_id': claim_id,
            'verdict': verdict,
            'summary': summary
        }
        
        return self.fact_check_repository.create_fact_check_with_sources(
            fact_check_data, sources
        )
    
    def get_fact_checks_for_claim(self, claim_id):
        """Get all fact checks for a claim"""
        return self.fact_check_repository.get_fact_checks_for_claim(claim_id)
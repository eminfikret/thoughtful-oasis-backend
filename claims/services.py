from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction

from .models import Claim
from .repositories import ClaimRepository, FactCheckRepository
from .utils import (
    check_claim_with_wikipedia,
    extract_claims_from_text,
    extract_claims_with_context,
    get_verdict_and_summary,
)


class ClaimService:
    """Service for handling claims and fact checking operations."""
    
    def __init__(self):
        """Initialize repositories."""
        self.claim_repository = ClaimRepository()
        self.fact_check_repository = FactCheckRepository()
    
    def process_raw_text(self, user_id: int, text: str) -> List[Dict[str, Any]]:
        """
        Process raw text to extract and fact-check claims.
        
        Args:
            user_id: User ID of the author
            text: Raw text to process
            
        Returns:
            List of claims with their fact check information
        """
        extracted_claims = extract_claims_from_text(text)
        
        if not extracted_claims:
            return []
            
        results = []

        with transaction.atomic():
            for idx, extracted_claim in enumerate(extracted_claims, 1):
                claim = self._create_claim(
                    user_id=user_id,
                    claim_text=extracted_claim,
                    source_type='raw',
                    source_id=None,
                    claim_index=idx,
                    source_text=text
                )
                
                fact_check_info = self._create_fact_check_for_claim(claim, extracted_claim)
                
                claim_data = self._format_claim_data(claim, basic=True)
                results.append({
                    "claim": claim_data,
                    "fact_check": fact_check_info
                })
                
        return results
    
    def process_content_for_claims(self, user_id: int, content: str, source_type: str, 
                                  source_id: int, context: dict = None) -> List[Dict[str, Any]]:
        """
        Process content to extract claims and create fact checks.
        
        Args:
            user_id: User ID of the author
            content: Text content to process
            source_type: Type of content source ('post', 'comment', or 'raw')
            source_id: ID of the post or comment
            context: Optional additional context (for comment threads)
            
        Returns:
            List of claims with their fact check information
        """
        if source_type not in ['post', 'comment', 'raw']:
            raise ValueError(f"Invalid source_type: {source_type}")
        
        # Use the new utility function that handles context when provided
        context_to_use = context if context and source_type == 'comment' else None
        extracted_claims = extract_claims_with_context(content, context_to_use)
        results = []
        
        with transaction.atomic():
            for i, claim_text in enumerate(extracted_claims, 1):
                claim = self._create_claim(
                    user_id=user_id,
                    claim_text=claim_text,
                    source_type=source_type,
                    source_id=source_id,
                    claim_index=i,
                    source_text=content if source_type == 'raw' else None
                )
                
                fact_check_info = self._create_fact_check_for_claim(claim, claim_text)
                
                claim_data = self._format_claim_data(claim, basic=True)
                results.append({
                    "claim": claim_data,
                    "fact_check": fact_check_info
                })
                
        return results
    
    def get_claim_with_fact_check(self, claim_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a claim with its associated fact check information.
        
        Args:
            claim_id: ID of the claim
            
        Returns:
            Dictionary with claim and fact check information, or None if claim not found
        """
        claim = self.claim_repository.get_claim_by_id(claim_id)
        if not claim:
            return None
            
        result = {"claim": self._format_claim_data(claim)}
        
        fact_check = self.fact_check_repository.get_fact_check_by_claim_id(claim.id)
        if fact_check:
            result["fact_check"] = self._format_fact_check_data(fact_check)
            
        return result
    
    def get_user_claims(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all claims created by a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of claims with their fact check information
        """
        claims = self.claim_repository.get_claims_for_user(user_id)
        results = []
        
        for claim in claims:
            result = {"claim": self._format_claim_data(claim)}
            
            fact_check = self.fact_check_repository.get_fact_check_by_claim_id(claim.id)
            if fact_check:
                result["fact_check"] = self._format_fact_check_data(fact_check)
            
            results.append(result)
            
        return results
    
    def get_claims_for_content(self, source_type: str, source_id: int) -> List[Dict[str, Any]]:
        """
        Get all claims for a specific post or comment.
        
        Args:
            source_type: Either 'post' or 'comment'
            source_id: ID of the post or comment
            
        Returns:
            List of claims with their fact check information
        """
        self._validate_source_type(source_type)
        
        claims = (Claim.objects.filter(post_id=source_id) if source_type == 'post' 
                 else Claim.objects.filter(comment_id=source_id))
        
        results = []
        for claim in claims:
            result = {"claim": self._format_claim_data(claim, include_source=False)}
            
            fact_check = self.fact_check_repository.get_fact_check_by_claim_id(claim.id)
            if fact_check:
                result["fact_check"] = self._format_fact_check_data(fact_check)
                
            results.append(result)
        
        return results
    
    def delete_claim(self, claim_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a claim (only if owned by the user).
        
        Args:
            claim_id: ID of the claim to delete
            user_id: ID of the user attempting to delete
            
        Returns:
            Tuple of (success, message)
        """
        claim = self.claim_repository.get_claim_by_id(claim_id)
        
        if not claim:
            return False, "Claim not found"
            
        if claim.user_id != user_id:
            return False, "You don't have permission to delete this claim"
            
        deleted = self.claim_repository.delete_claim(claim_id)
        
        return (True, "Claim deleted successfully") if deleted else (False, "Error deleting claim")
    
    def delete_claims_for_content(self, source_type: str, source_id: int) -> int:
        """
        Delete all claims for a specific post or comment.
        
        Args:
            source_type: Either 'post' or 'comment'
            source_id: ID of the post or comment
            
        Returns:
            Number of claims deleted
        """
        if source_type not in ['post', 'comment']:
            raise ValueError(f"Invalid source_type: {source_type}. Must be 'post' or 'comment'")
        
        claims = (Claim.objects.filter(post_id=source_id) if source_type == 'post'
                 else Claim.objects.filter(comment_id=source_id))
        
        count = claims.count()
        claims.delete()
        return count
    
    def create_mock_claims(self, content: str, source_type: str, source_id: int, 
                           user_id: int = None) -> List[Claim]:
        """
        Create mock claims and fact checks for testing purposes.
        
        Args:
            content: Text content
            source_type: Type of content source ('post' or 'comment')
            source_id: ID of the post or comment
            user_id: Optional user ID
            
        Returns:
            List of created mock claims
        """
        num_claims = min(2, max(1, len(content) // 100))
        created_claims = []
        
        for i in range(num_claims):
   
            claim_text = f"Mock claim #{i+1} for testing purposes from: {content[:30]}..."
            claim = self._create_claim(
                user_id=user_id,
                claim_text=claim_text,
                source_type=source_type,
                source_id=source_id,
                claim_index=i+1
            )
            
            verdict = "supported" if i % 2 == 0 else "contradicted"
            fact_check = self.fact_check_repository.create_fact_check(
                claim_id=claim.id,
                verdict=verdict,
                summary=f"This is a mock {verdict} summary for testing purposes."
            )
            
            self.fact_check_repository.create_fact_check_source(
                fact_check_id=fact_check.id,
                url="https://en.wikipedia.org/wiki/Mock",
                title="Mock - Wikipedia",
                description="This is a mock Wikipedia result for testing",
                relevance_score=0.95
            )
            
            created_claims.append(claim)
        
        return created_claims
    
    def _create_claim(self, user_id: int, claim_text: str, source_type: str, 
                     source_id: int = None, claim_index: int = 1, 
                     source_text: str = None) -> Claim:
        """Create a new claim."""
        claim_kwargs = {
            'user_id': user_id,
            'extracted_claim': claim_text,
            'source_type': source_type,
            'claim_index': claim_index
        }
        
        if source_type == 'post':
            claim_kwargs['post_id'] = source_id
        elif source_type == 'comment':
            claim_kwargs['comment_id'] = source_id
        elif source_type == 'raw' and source_text:
            claim_kwargs['source_text'] = source_text
        
        return self.claim_repository.create_claim(**claim_kwargs)
    
    def _create_fact_check_for_claim(self, claim: Claim, claim_text: str) -> Dict[str, Any]:
        """Create a fact check for a claim and return formatted data."""
        wiki_result = check_claim_with_wikipedia(claim_text)
        evidence = wiki_result["evidence"]
        sources = wiki_result["sources"]

        verdict_result = get_verdict_and_summary(claim_text, evidence)
        verdict = verdict_result["verdict"]
        summary = verdict_result["summary"]

        fact_check = self.fact_check_repository.create_fact_check(
            claim_id=claim.id,
            verdict=verdict,
            summary=summary
        )

        fact_check_sources = []
        for source in sources:
            fact_check_source = self.fact_check_repository.create_fact_check_source(
                fact_check_id=fact_check.id,
                url=source["url"],
                title=source["title"],
                description=source["description"],
                relevance_score=source["relevance_score"]
            )
            fact_check_sources.append({
                "id": fact_check_source.id,
                "url": fact_check_source.url,
                "title": fact_check_source.title,
                "description": source["description"]
            })
            
        return {
            "id": fact_check.id,
            "verdict": fact_check.verdict,
            "summary": fact_check.summary,
            "sources": fact_check_sources
        }
    
    def _format_claim_data(self, claim: Claim, basic: bool = False, 
                          include_source: bool = True) -> Dict[str, Any]:
        """Format claim data for API responses."""
        claim_data = {
            "id": claim.id,
            "extracted_claim": claim.extracted_claim,
            "source_type": claim.source_type,
            "claim_index": claim.claim_index
        }
        
        if not basic:
            claim_data["created_at"] = claim.created_at
            
        if include_source:
            if claim.source_type == 'post' and claim.post_id:
                claim_data["post_id"] = claim.post_id
            elif claim.source_type == 'comment' and claim.comment_id:
                claim_data["comment_id"] = claim.comment_id
            elif claim.source_type == 'raw' and claim.source_text:
                claim_data["source_text"] = claim.source_text
                
        return claim_data
    
    def _format_fact_check_data(self, fact_check) -> Dict[str, Any]:
        """Format fact check data for API responses."""
        sources = fact_check.sources.all()
        return {
            "id": fact_check.id,
            "verdict": fact_check.verdict,
            "summary": fact_check.summary,
            "created_at": fact_check.created_at,
            "sources": [
                {
                    "id": source.id,
                    "url": source.url,
                    "title": source.title,
                    "description": source.description
                } for source in sources
            ]
        }
    
    def _validate_source_type(self, source_type: str) -> None:
        """Validate that source type is either 'post' or 'comment'."""
        if source_type not in ['post', 'comment']:
            raise ValueError(f"Invalid source_type: {source_type}. Must be 'post' or 'comment'")
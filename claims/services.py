from typing import List, Dict, Any, Optional, Tuple
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor

from .repositories import ClaimRepository, FactCheckRepository
from .utils import extract_claims_from_text, check_claim_with_wikipedia, get_verdict_and_summary


class ClaimService:
    """Service for handling claims and fact checking"""
    
    def __init__(self):
        self.claim_repository = ClaimRepository()
        self.fact_check_repository = FactCheckRepository()
    
    def process_raw_text(self, user_id: int, text: str) -> List[Dict[str, Any]]:
        """
        Process raw text to extract claims and perform fact checking
        
        Args:
            user_id: ID of the user submitting the text
            text: Raw text to process
            
        Returns:
            List of dictionaries with claim and fact check information
        """
   
        extracted_claims = extract_claims_from_text(text)
        
        if not extracted_claims:
            return []
            
        results = []

        with transaction.atomic():
            for idx, extracted_claim in enumerate(extracted_claims, 1):

                claim = self.claim_repository.create_claim(
                    user_id=user_id,
                    source_type='raw',
                    extracted_claim=extracted_claim,
                    claim_index=idx,
                    source_text=text
                )

                wiki_result = check_claim_with_wikipedia(extracted_claim)
                evidence = wiki_result["evidence"]
                sources = wiki_result["sources"]

                verdict_result = get_verdict_and_summary(extracted_claim, evidence)
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
                        "title": fact_check_source.title
                    })

                results.append({
                    "claim": {
                        "id": claim.id,
                        "extracted_claim": claim.extracted_claim,
                        "claim_index": claim.claim_index
                    },
                    "fact_check": {
                        "id": fact_check.id,
                        "verdict": fact_check.verdict,
                        "summary": fact_check.summary,
                        "sources": fact_check_sources
                    }
                })
                
        return results
    
    def process_content_for_claims(self, user_id: int, content: str, source_type: str, source_id: int) -> List[Dict[str, Any]]:
        """
        Process content from a post or comment to extract and fact-check claims
        
        Args:
            user_id: ID of the user who created the post/comment
            content: Text content to process
            source_type: Either 'post' or 'comment'
            source_id: ID of the post or comment
            
        Returns:
            List of dictionaries with claim and fact check information
        """
        if source_type not in ['post', 'comment']:
            raise ValueError(f"Invalid source_type: {source_type}. Must be 'post' or 'comment'")
        
        extracted_claims = extract_claims_from_text(content)
        
        if not extracted_claims:
            return []
            
        results = []

        with transaction.atomic():
            for idx, extracted_claim in enumerate(extracted_claims, 1):
                claim_kwargs = {
                    'user_id': user_id,
                    'source_type': source_type,
                    'extracted_claim': extracted_claim,
                    'claim_index': idx
                }
                
                if source_type == 'post':
                    claim_kwargs['post_id'] = source_id
                else:  
                    claim_kwargs['comment_id'] = source_id
                
                claim = self.claim_repository.create_claim(**claim_kwargs)

                wiki_result = check_claim_with_wikipedia(extracted_claim)
                evidence = wiki_result["evidence"]
                sources = wiki_result["sources"]

                verdict_result = get_verdict_and_summary(extracted_claim, evidence)
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
                        "title": fact_check_source.title
                    })

                results.append({
                    "claim": {
                        "id": claim.id,
                        "extracted_claim": claim.extracted_claim,
                        "claim_index": claim.claim_index
                    },
                    "fact_check": {
                        "id": fact_check.id,
                        "verdict": fact_check.verdict,
                        "summary": fact_check.summary,
                        "sources": fact_check_sources
                    }
                })
                
        return results

    def get_claim_with_fact_check(self, claim_id: int) -> Optional[Dict[str, Any]]:
        """
        Get claim details along with fact check information
        
        Args:
            claim_id: ID of the claim
            
        Returns:
            Dictionary with claim and fact check information, or None if not found
        """
        claim = self.claim_repository.get_claim_by_id(claim_id)
        if not claim:
            return None
            
        result = {
            "claim": {
                "id": claim.id,
                "extracted_claim": claim.extracted_claim,
                "source_type": claim.source_type,
                "created_at": claim.created_at,
                "claim_index": claim.claim_index
            }
        }

        if claim.source_type == 'post' and claim.post_id:
            result["claim"]["post_id"] = claim.post_id
        elif claim.source_type == 'comment' and claim.comment_id:
            result["claim"]["comment_id"] = claim.comment_id
        elif claim.source_type == 'raw':
            result["claim"]["source_text"] = claim.source_text

        fact_check = self.fact_check_repository.get_fact_check_by_claim_id(claim.id)
        if fact_check:
            sources = fact_check.sources.all()
            result["fact_check"] = {
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
            
        return result
    
    def get_user_claims(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all claims for the current user
        
        Args:
            user_id: ID of the current user
            
        Returns:
            List of claims with their fact check information
        """
        claims = self.claim_repository.get_claims_for_user(user_id)
        results = []
        
        for claim in claims:
            claim_data = {
                "id": claim.id,
                "extracted_claim": claim.extracted_claim,
                "source_type": claim.source_type,
                "created_at": claim.created_at,
                "claim_index": claim.claim_index
            }
            
            if claim.source_type == 'post' and claim.post_id:
                claim_data["post_id"] = claim.post_id
            elif claim.source_type == 'comment' and claim.comment_id:
                claim_data["comment_id"] = claim.comment_id
            elif claim.source_type == 'raw':
                claim_data["source_text"] = claim.source_text
                
            fact_check = self.fact_check_repository.get_fact_check_by_claim_id(claim.id)
            
            result = {"claim": claim_data}
            
            if fact_check:
                sources = fact_check.sources.all()
                result["fact_check"] = {
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
            
            results.append(result)
            
        return results
    
    def delete_claim(self, claim_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a claim and its associated fact check
        
        Args:
            claim_id: ID of the claim to delete
            user_id: ID of the user requesting deletion
            
        Returns:
            Tuple of (success, message)
        """
        claim = self.claim_repository.get_claim_by_id(claim_id)
        
        if not claim:
            return False, "Claim not found"
            
        if claim.user_id != user_id:
            return False, "You don't have permission to delete this claim"
            
        deleted = self.claim_repository.delete_claim(claim_id)
        
        if deleted:
            return True, "Claim deleted successfully"
        else:
            return False, "Error deleting claim"
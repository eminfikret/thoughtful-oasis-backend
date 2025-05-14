import asyncio
from concurrent.futures import ThreadPoolExecutor

from .services import ClaimService

_executor = ThreadPoolExecutor(max_workers=3)
claim_service = ClaimService()

def extract_claims_sync(content, source_type, source_id):
    """
    Extract claims from content synchronously
    
    Args:
        content (str): Text content to analyze
        source_type (str): Either 'post' or 'comment'
        source_id (int): ID of the post or comment
        
    Returns:
        list: List of created claim objects
    """
    return claim_service.process_content_for_claims(content, source_type, source_id)


async def extract_claims_async(content, source_type, source_id):
    """
    Extract claims from content asynchronously
    
    Args:
        content (str): Text content to analyze
        source_type (str): Either 'post' or 'comment'
        source_id (int): ID of the post or comment
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        _executor,
        lambda: claim_service.process_content_for_claims(content, source_type, source_id)
    )

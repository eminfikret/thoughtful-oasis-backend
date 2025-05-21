"""Mock response generators for API testing."""

def mock_llm_response(text_content):
    """
    Create a mock LLM API response with the given text content.
    
    Args:
        text_content: The text to include in the response
        
    Returns:
        Dict representing the LLM API response structure
    """
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": text_content}
                    ]
                }
            }
        ]
    }

def mock_extract_claims_response(claims):
    """
    Create a mock LLM response for claim extraction.
    
    Args:
        claims: List of claim texts to include
        
    Returns:
        Text string formatted as the LLM would return for extraction
    """
    response_lines = []
    for claim in claims:
        response_lines.append(f"CLAIM: {claim}")
    return "\n".join(response_lines)

def mock_verdict_and_summary_response(verdict, summary):
    """
    Create a mock LLM response for verdict and summary generation.
    
    Args:
        verdict: The verdict (supported, contradicted, or not_found)
        summary: The summary text
        
    Returns:
        Text string formatted as the LLM would return for verdicts
    """
    return f"Verdict: {verdict}\nSummary: {summary}"

def mock_wikipedia_response(has_results=True, page_title="Test Page", page_content="Test content for evidence."):
    """
    Create a mock Wikipedia API response.
    
    Args:
        has_results: Whether the response should contain results
        page_title: Title of the Wikipedia page
        page_content: Content of the Wikipedia page for evidence
        
    Returns:
        Dict representing a Wikipedia API response
    """
    if not has_results:
        return {"query": {"search": []}}
    
    return {
        "query": {
            "search": [
                {
                    "title": page_title,
                    "snippet": "Snippet from Wikipedia article",
                    "pageid": 12345
                }
            ]
        },
        "parse": {
            "title": page_title,
            "pageid": 12345,
            "text": {"*": page_content}
        }
    }
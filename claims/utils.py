import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

LLM_URL = os.environ.get("LLM_URL", "")
WIKIPEDIA_API_URL = os.environ.get("WIKIPEDIA_API_URL", "")

def call_llm(prompt: str) -> str:
    """Call LLM API with the given prompt"""
    headers = {"Content-Type": "application/json"}
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(LLM_URL, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        raise RuntimeError(f"Failed to process with LLM: {str(e)}")

def extract_claims_from_text(text: str) -> List[str]:
    """Extract factual claims from text using LLM"""
    prompt = f"""Extract only the **main factual claims explicitly asserted** in the following text.

    A **factual claim** is a specific assertion about the external world that can be independently verified using objective evidence.

    ### IMPORTANT RULES:

    - Only include **claims that the speaker directly asserts or implies as their main point**.
    - **Do NOT extract background facts** or context unless the speaker is **clearly asserting them as claims**.
    - Do NOT include claims about the speaker/writer themselves (e.g., their job, location, appearance, or personal experiences).
    - Do NOT include statements that start with or imply "I", "my", "we", "us", or any form of personal reference.
    - Do NOT include opinions, subjective descriptions, or unverifiable experiences.
    - Do NOT infer multiple claims from one sentence unless **each is clearly presented as a distinct assertion**.

    ### EXAMPLES:

    Input: "I'm a nurse in Chicago. I see a lot of flu cases every winter."
    Output:
    CLAIM: Flu cases increase every winter in Chicago.

    Input: "Yorkshire pudding is the best part of a Sunday roast."
    Output:
    (No output — this is a subjective opinion.)

    Input: "Yorkshire pudding is a food from England that people have been eating since the 1700s."
    Output:
    CLAIM: Yorkshire pudding is a food from England.
    CLAIM: People have been eating Yorkshire pudding since the 1700s.

    Now apply this to the following text:

    Text: {text}

    List each **clearly asserted** claim on a new line starting with "CLAIM:".
    If there are **no clear factual claims**, write: (No factual claims found.)
    """ # noqa: E501
    result = call_llm(prompt)
    claims = []
    for line in result.split("\n"):
        if line.strip().lower().startswith("claim:"):
            claim = line.split(":", 1)[1].strip()
            if len(claim) > 2: 
                claims.append(claim)
    return claims

def check_claim_with_wikipedia(claim: str) -> Dict[str, Any]:
    """Check a claim against Wikipedia and return evidence and source data"""
    try:
        response = requests.post(
            WIKIPEDIA_API_URL, 
            json={"query": claim, "limit": 3}
        )
        response.raise_for_status()
        data = response.json().get("results", [])
        
        evidence = ""
        sources = []
        
        if not data:
            evidence = "No relevant Wikipedia data found."
        else:
            for idx, result in enumerate(data, 1):
                title = result.get("title", "")
                snippet = result.get("text", "")
                url = result.get("url", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")
                
                evidence += f"{idx}. {title}: {snippet}\n\n"
                
                # Store source information
                sources.append({
                    "url": url,
                    "title": title,
                    "description": snippet,
                    "relevance_score": result.get("score", None)
                })
        
        return {
            "evidence": evidence.strip(),
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Error fetching Wikipedia data: {e}")
        return {
            "evidence": f"Error fetching Wikipedia data: {str(e)}",
            "sources": []
        }

def get_verdict_and_summary(claim: str, evidence: str) -> Dict[str, str]:
    """Generate verdict and summary for a claim based on evidence"""
    prompt = f"""You are given a factual CLAIM and evidence from Wikipedia.
Based on the evidence, determine the most likely classification:
- "supported"
- "contradicted"
- "not_found"

Use "not_found" when there is insufficient evidence from Wikipedia to assess whether the claim is true or false.

Also provide a short explanation in the summary. Your summary must be in the tone of addressing the original claim made. 
When referring to the wikipedia evidence, refer to it as "available evidence". So for example you can say "the available evidence suggests".
Use Direct Quotes from the evidence too.

CLAIM: {claim}

EVIDENCE:
{evidence}

Respond in this format:
Verdict: <one of supported, contradicted, not_found>
Summary: <short explanation>
"""  # noqa: E501
    result = call_llm(prompt)

    lines = result.strip().split('\n')
    verdict = ""
    summary = ""
    
    for line in lines:
        if line.lower().startswith("verdict:"):
            verdict = line.split(":", 1)[1].strip().lower()
        elif line.lower().startswith("summary:"):
            summary = line.split(":", 1)[1].strip()
            summary_index = lines.index(line)
            if summary_index < len(lines) - 1:
                summary += "\n" + "\n".join(lines[summary_index + 1:])

    if verdict not in ["supported", "contradicted", "not_found"]:
        if "support" in verdict:
            verdict = "supported"
        elif "contradict" in verdict:
            verdict = "contradicted"
        else:
            verdict = "not_found"
    
    return {
        "verdict": verdict,
        "summary": summary
    }

_executor = ThreadPoolExecutor(max_workers=3)

def extract_claims_sync(content, source_type, source_id):
    """
    Extract claims from content synchronously
    
    Args:
        content (str): Text content to analyse
        source_type (str): Either 'post' or 'comment'
        source_id (int): ID of the post or comment
        
    Returns:
        list: List of created claim objects
    """
    from .services import ClaimService
    claim_service = ClaimService()
    
    return claim_service.process_content_for_claims(content, source_type, source_id)


async def extract_claims_async(content, source_type, source_id):
    """
    Extract claims from content asynchronously
    
    Args:
        content (str): Text content to analyse
        source_type (str): Either 'post' or 'comment'
        source_id (int): ID of the post or comment
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        _executor,
        lambda: extract_claims_sync(content, source_type, source_id)
    )

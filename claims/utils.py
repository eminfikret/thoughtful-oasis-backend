import asyncio
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

LLM_URL = os.environ.get("LLM_URL", "")
WIKIPEDIA_API_URL = os.environ.get("WIKIPEDIA_API_URL", "")

def call_llm(prompt: str) -> str:
    """Call LLM API with the given prompt"""
    headers = {"Content-Type": "application/json"}
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
     
        response = requests.post(LLM_URL, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from LLM API: {e}")
        return "FALLBACK_RESPONSE"
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        return "FALLBACK_RESPONSE"

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
    - **EACH CLAIM MUST BE COMPLETELY SELF-CONTAINED** with all necessary context included.
    - **RESOLVE ALL PRONOUNS AND REFERENCES** to ensure claims stand alone without additional context.

    ### EXAMPLES OF SELF-CONTAINED CLAIMS:

    Input: "It crashed last year and caused billions in damage."
    BAD CLAIM: It crashed last year. (unclear what "it" refers to)
    GOOD CLAIM: The stock market crashed in 2025 and caused billions in damage.

    Input: "These animals can survive there for months without food."
    BAD CLAIM: These animals can survive for months without food. (unclear which animals)
    GOOD CLAIM: Polar bears can survive in Arctic conditions for months without food.

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

    List each **clearly asserted, self-contained claim** on a new line starting with "CLAIM:".
    Every claim must be fully understandable on its own without requiring additional context.
    If there are **no clear factual claims**, write: (No factual claims found.)

    If it is unclear what the speaker is referring to (even with all the context provided),
    do NOT extract a claim.
    """ # noqa: E501
    
    try:
        result = call_llm(prompt)
        if result == "FALLBACK_RESPONSE":
            logger.warning("Using fallback for claim extraction due to LLM service unavailability")
            return ["Service temporarily unavailable."]
            
        claims = []
        for line in result.split("\n"):
            if line.strip().lower().startswith("claim:"):
                claim = line.split(":", 1)[1].strip()
                if len(claim) > 2: 
                    claims.append(claim)
        return claims
    except Exception as e:
        logger.error(f"Failed to extract claims: {e}")
        return ["Service temporarily unavailable."]

def check_claim_with_wikipedia(claim: str) -> Dict[str, Any]:
    """Check a claim against Wikipedia and return evidence and source data"""
    try:
 
        response = requests.post(
            WIKIPEDIA_API_URL, 
            json={"query": claim, "limit": 3},
            timeout=60
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
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Wikipedia API request failed: {e}")
        return {
            "evidence": "Wikipedia service is temporarily unavailable.",
            "sources": [{
                "url": "",
                "title": "Service Unavailable",
                "description": "The Wikipedia evidence service is temporarily unavailable.",
                "relevance_score": None
            }]
        }
    except Exception as e:
        
        logger.error(f"Error fetching Wikipedia data: {e}")
        return {
            "evidence": "Unable to retrieve evidence from Wikipedia.",
            "sources": [{
                "url": "",
                "title": "Error",
                "description": "An error occurred while retrieving evidence.",
                "relevance_score": None
            }]
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

IMPORTANT FOR QUOTATIONS:
- Use ONLY EXACT, VERBATIM quotes from the evidence.
- Place all direct quotes in double quotation marks.
- DO NOT paraphrase, modify, or adjust ANY quotation in ANY way.
- ONLY quote text that appears EXACTLY as written in the evidence.
- If you cannot find an exact quote that supports your point, do not use quotation marks.
- Every single character within quotation marks must match the evidence precisely.

IMPORTANT FOR RELEVANCE:
1. Only refer to evidence that is DIRECTLY RELEVANT to the claim.
2. DO NOT mention unrelated information from the evidence in your summary.
3. If parts of the evidence are irrelevant to the claim, ignore those parts completely.
4. If none of the evidence is relevant to the specific claim, use "not_found" verdict and explain that the evidence doesn't address the claim.
5. Focus only on verifying the exact claim provided, not tangential aspects.

CLAIM: {claim}

EVIDENCE:
{evidence}

Respond in this format:
Verdict: <one of supported, contradicted, not_found>
Summary: <short explanation focusing ONLY on relevant evidence and using ONLY EXACT quotes>
"""  # noqa: E501
    
    max_retries = 4
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            result = call_llm(prompt)
            if result == "FALLBACK_RESPONSE":
                return {
                    "verdict": "not_found",
                    "summary": "This is an automatic fallback response due to service "
                    "unavailability."
                }
                
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
            
            if _verify_quotes_in_evidence(summary, evidence):
                return {
                    "verdict": verdict,
                    "summary": summary
                }
            
            logger.warning(f"Quote verification failed on attempt {retry_count + 1}. Retrying...")
            retry_count += 1
            
            prompt += (
                f"\n\nWARNING: Your previous response contained quotes that DO NOT EXACTLY match "
                f"the evidence. Review the evidence again carefully and ONLY use EXACT quotes "
                f"that appear verbatim in the evidence. This is attempt "
                f"{retry_count + 1} of {max_retries}."
            )
            
        except Exception as e:
            logger.error(f"Failed to get verdict: {e}")
            return {
                "verdict": "not_found",
                "summary": "This is an automatic fallback response due to service unavailability."
            }
    
    logger.error(f"Failed to generate summary with valid quotes after {max_retries} attempts")
    return {
        "verdict": "not_found",
        "summary": "Unable to generate a summary with accurate quotations. Please try again later."
    }

def _verify_quotes_in_evidence(summary: str, evidence: str) -> bool:
    """
    Verify that all quoted text in summary appears exactly in the evidence.
    
    Args:
        summary: The summary text containing quotes
        evidence: The evidence text to check against
        
    Returns:
        True if all quotes match exactly, False otherwise
    """
    quoted_texts = re.findall(r'"([^"]*)"', summary)
    
    if not quoted_texts:
        return True
    
    evidence_lower = evidence.lower()
    
    for quote in quoted_texts:
        if not quote.strip(): 
            continue
            
        if quote.lower() not in evidence_lower:
            logger.warning(f"Quote verification failed: '{quote}' not found in evidence")
            return False
    
    return True

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

def extract_claims_with_context(content: str, context: dict = None) -> List[str]:
    """
    Extract factual claims from content with optional context
    
    Args:
        content: Text content to extract claims from
        context: Optional context for comments (post and conversation thread)
        
    Returns:
        List of extracted factual claims
    """
    prompt = _create_content_prompt(content, context)
    
    try:
        return extract_claims_from_text(prompt)
    except Exception as e:
        logger.error(f"Error extracting claims with context: {e}")
        return ["Service temporarily unavailable."]

def _create_content_prompt(content: str, context: dict = None) -> str:
    """
    Create appropriate prompt for claim extraction based on content type
    
    Args:
        content: Text content to analyze
        context: Optional context for comments
        
    Returns:
        Formatted prompt string
    """
    if not context:
        return "\n".join([
            "You are a fact-checking assistant. Extract factual claims from the following text:",
            "",
            content,
            "",
            "Extract all factual claims that can be fact-checked from the text above.",
            "These should be statements asserting facts that can be verified, not opinions or"
            " questions.",
            "Return the extracted claims as a JSON list of strings.",
            "If there are no factual claims to extract, return an empty JSON list: []"
        ])
    else:
        prompt_parts = [
            "You are a fact-checking assistant analyzing a conversation thread.",
            "",
            f"POST TITLE: {context['post']['title']}",
            f"POST CONTENT: {context['post']['content']}",
            "",
            "CONVERSATION THREAD:"
        ]
        
        if context.get('conversation_thread'):
            for i, comment in enumerate(context['conversation_thread']):
                prefix = "  " * comment.get('depth', 0) 
                prompt_parts.append(
                    f"{prefix}[Comment {i+1} by {comment['author']}]: {comment['content']}"
                )
        
        prompt_parts.extend([
            "",
            "TARGET COMMENT (the one to analyze):",
            f"{content}",
            "",
            "INSTRUCTIONS:",
            "1. Extract ONLY factual claims made in the TARGET COMMENT above.",
            "2. Consider the FULL CONTEXT of the conversation when determining what claims"
            " are being made.",
            "3. Include implicit claims where the target comment agrees with or refers to facts "
            "stated elsewhere.",
            "4. If the target comment says 'That's right' or similar in response to a factual"
            " claim, extract the claim being agreed with.",
            "5. Do NOT extract claims from other comments unless explicitly endorsed in the "
            "target comment.",
            "6. For each extracted claim, make sure it is a complete statement that can be"
            " fact-checked.",
            "",
            "List each claim on a new line starting with 'CLAIM:'.",
            "If there are no factual claims (explicit or implicit) in the TARGET COMMENT, respond"
            " with: (No factual claims found.)"
        ])
        
        return "\n".join(prompt_parts)

def generate_claim_linked_xml(post_content: str, claims: list) -> str:
    """
    Generate XML that links parts of the post content to specific claims.
    
    Args:
        post_content: The full text of the post
        claims: List of claim objects with id, extracted_claim, and verdict
        
    Returns:
        XML string with claim links embedded in the post content or None if LLM fails
    """
    if not claims:
        return f"<text>{post_content}</text>"
    
    claim_texts = [
        f"{claim['claim']['id']}:{claim['claim']['extracted_claim']}"
        for claim in claims
    ]
    claims_list = "\n".join([f"{i+1}. ID {claim_id}: {claim_text}" for i, (claim_id, claim_text) in 
                           enumerate([c.split(":", 1) for c in claim_texts])])
    
    prompt = f"""
    Original Text:
    "{post_content}"
    
    Claims to link (with their IDs):
    {claims_list}
    
    For each claim listed above, find the EXACT segment of text in the original content that 
    most closely corresponds to that claim.
    
    IMPORTANT:
    - Return ONLY exact text segments that appear in the original text
    - DO NOT paraphrase or modify the text in any way
    - If multiple claims refer to the same text, select the most contextually important
      claim for that segment
    - If a claim has no clear text segment match, respond with "NO_MATCH" for that claim
    
    Format your response as follows (one line per claim):
    CLAIM_ID:EXACT_TEXT_SEGMENT
    
    Example:
    25:This is the exact text from the original content
    42:Another exact segment from the original text
    56:NO_MATCH
    """
    
    llm_response = call_llm(prompt).strip()
    
    if llm_response == "FALLBACK_RESPONSE":
        logger.warning("LLM failed while generating claim-linked XML, returning None")
        return None
    
    segments = []
    claim_id_to_text = {}
    
    for line in llm_response.split('\n'):
        line = line.strip()
        if not line or ':' not in line:
            continue
            
        parts = line.split(':', 1)
        if len(parts) != 2:
            continue
            
        claim_id_part, segment_text = parts
        
        try:
            claim_id = int(re.search(r'\d+', claim_id_part).group())
        except (ValueError, AttributeError):
            continue
            
        if segment_text == "NO_MATCH":
            continue
            
        if segment_text in post_content:
            segments.append({
                "id": claim_id,
                "text": segment_text,
                "start_index": post_content.index(segment_text)
            })
            claim_id_to_text[claim_id] = segment_text
    
    for claim in claims:
        claim_id = claim["claim"]["id"]
        if claim_id not in claim_id_to_text:
            claim_text = claim["claim"]["extracted_claim"]
            
            if claim_text in post_content:
                segments.append({
                    "id": claim_id,
                    "text": claim_text,
                    "start_index": post_content.index(claim_text)
                })
            else:
                key_words = [w for w in claim_text.split() if len(w) > 3]
                for word in key_words:
                    found_match = False
                    for sentence in re.split(r'[.!?]', post_content):
                        if word.lower() in sentence.lower():
                            potential_segment = sentence.strip()
                            if len(potential_segment) > 3 and potential_segment in post_content:
                                segments.append({
                                    "id": claim_id,
                                    "text": potential_segment,
                                    "start_index": post_content.index(potential_segment)
                                })
                                found_match = True
                                break
                    if found_match:
                        break
    
    segments.sort(key=lambda x: x["start_index"])
    
    processed_segments = []
    if segments:
        processed_segments = [segments[0]]
        
        for i in range(1, len(segments)):
            current = segments[i]
            previous = processed_segments[-1]
            
            current_start = current["start_index"]
            current_end = current_start + len(current["text"])
            previous_end = previous["start_index"] + len(previous["text"])
            
            if current_start < previous_end:
                overlap_size = previous_end - current_start
                overlap_ratio = overlap_size / len(current["text"])
                
                if overlap_ratio > 0.5:
                    if len(current["text"]) < len(previous["text"]):
                        processed_segments[-1] = current
                    continue
                
                if current_end > previous_end:
                    for break_point in range(previous_end-1, current_start-1, -1):
                        if post_content[break_point] in " ,.;:!?":
                            previous["text"] = post_content[previous["start_index"]:break_point+1]
                            current["start_index"] = break_point+1
                            current["text"] = post_content[break_point+1:current_end]
                            processed_segments.append(current)
                            break
                    else:
                        middle = (current_start + previous_end) // 2
                        previous["text"] = post_content[previous["start_index"]:middle]
                        current["start_index"] = middle
                        current["text"] = post_content[middle:current_end]
                        processed_segments.append(current)
            else:
                processed_segments.append(current)
    
    result = "<text>"
    last_end = 0
    
    for segment in processed_segments:
        start = segment["start_index"]
        end = start + len(segment["text"])
        
        if start > last_end:
            result += post_content[last_end:start]
            
        result += f'<link id="{segment["id"]}">{segment["text"]}</link>'
            
        last_end = end
    
    if last_end < len(post_content):
        result += post_content[last_end:]
        
    result += "</text>"
    return result

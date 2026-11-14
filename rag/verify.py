import re
from typing import List, Dict, Any

def verify_claims(draft: str, evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Splits a draft into atomic sentence claims and labels each claim against retrieved evidence:
    - 'supported': key facts/skills/projects are grounded in evidence
    - 'partly_supported': overlapping domain keywords present, but missing direct match
    - 'unsupported': no matching keywords or facts found in evidence
    """
    if not draft or not draft.strip():
        return []

    # Split draft into sentences/atomic claims
    raw_claims = [c.strip() for c in re.split(r'(?<=[.!?])\s+', draft) if c.strip()]
    
    # Combine all evidence content into a single searchable text blob
    evidence_text = " ".join([
        f"{e.get('content', '')} {e.get('metadata', '')}"
        for e in evidence
    ]).lower()

    claim_results = []

    for claim in raw_claims:
        claim_lower = claim.lower()
        # Extract meaningful alphanumeric terms (length > 3)
        terms = set(re.findall(r'\b[a-z0-9_-]{4,}\b', claim_lower))
        
        # Filter out generic stop words
        stopwords = {"with", "that", "this", "from", "have", "been", "will", "your", "project", "using", "such"}
        meaningful_terms = terms - stopwords

        if not meaningful_terms:
            status = "supported"
            matching_terms = []
        else:
            matching_terms = [t for t in meaningful_terms if t in evidence_text]
            match_ratio = len(matching_terms) / len(meaningful_terms)

            if match_ratio >= 0.5:
                status = "supported"
            elif match_ratio > 0.0:
                status = "partly_supported"
            else:
                status = "unsupported"

        claim_results.append({
            "claim": claim,
            "status": status,
            "matching_terms": matching_terms
        })

    return claim_results

if __name__ == "__main__":
    print("Testing rag/verify.py claim verification...")
    
    sample_draft = "I have built customer churn classification models using Python and scikit-learn. I also have 10 years of experience with quantum computing."
    sample_evidence = [{
        "content": "Title: Customer churn classification coursework\nDescription: Built ML model\nTechnologies: Python, scikit-learn, classification"
    }]

    results = verify_claims(sample_draft, sample_evidence)
    print(f"\nVerified {len(results)} claims:\n")
    for r in results:
        print(f"[{r['status'].upper()}] Claim: \"{r['claim']}\"")
        print(f"  Matching terms: {r['matching_terms']}\n")
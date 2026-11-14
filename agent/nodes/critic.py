import sys
from pathlib import Path
from typing import List
from agent.state import GigBidState

# Path inclusion to access rag.verify
sys.path.append(str(Path(__file__).parent.parent.parent))
from rag.verify import verify_claims

def critic_node(state: GigBidState) -> GigBidState:
    """
    Critic Node: Evaluates the draft for factual grounding against evidence using
    rag/verify.py. Allows up to 2 revisions if unsupported claims are found.
    """
    proposal_draft = state.get("proposal_draft", {})
    evidence = state.get("evidence", [])
    critique = state.get("critique", {})
    errors: List[str] = list(state.get("errors", []))

    revision_count = critique.get("revision_count", 0)
    cover_letter = proposal_draft.get("cover_letter", "")

    # Run claim verification logic
    claim_verifications = verify_claims(cover_letter, evidence)
    
    unsupported_claims = [c for c in claim_verifications if c.get("status") == "unsupported"]
    
    if unsupported_claims and revision_count < 2:
        approved = False
        feedback = f"Found {len(unsupported_claims)} unsupported claim(s). Revision requested."
        revision_count += 1
    else:
        approved = True
        feedback = "Draft meets factual grounding standards."

    critique_result = {
        "approved": approved,
        "feedback": feedback,
        "revision_count": revision_count,
        "unsupported_count": len(unsupported_claims)
    }

    print(f"🧐 [Critic] Approved: {approved} | Revision Count: {revision_count} | Unsupported Claims: {len(unsupported_claims)}")

    return {
        **state,
        "claim_verification": claim_verifications,
        "critique": critique_result,
        "errors": errors
    }
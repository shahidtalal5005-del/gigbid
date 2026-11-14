import re
from typing import List
from agent.state import GigBidState

def compliance_node(state: GigBidState) -> GigBidState:
    """
    Compliance Node: Validates proposal content against policy constraints
    (e.g., prohibiting off-platform contact details, email addresses, phone numbers).
    """
    proposal_draft = state.get("proposal_draft", {})
    errors: List[str] = list(state.get("errors", []))

    cover_letter = proposal_draft.get("cover_letter", "")
    violations = []

    # Check for direct email addresses or phone numbers in text
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', cover_letter):
        violations.append("EMAIL_EXPOSURE")

    if re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', cover_letter):
        violations.append("PHONE_EXPOSURE")

    passed = len(violations) == 0

    compliance_verdict = {
        "passed": passed,
        "violations": violations,
        "summary": "Compliance check passed cleanly." if passed else f"Violations found: {', '.join(violations)}"
    }

    print(f"🛡️ [Compliance] Passed: {passed} | Violations: {violations}")

    return {
        **state,
        "compliance_verdict": compliance_verdict,
        "errors": errors
    }
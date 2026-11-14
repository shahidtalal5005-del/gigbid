from typing import List
from agent.state import GigBidState

def client_liaison_node(state: GigBidState) -> GigBidState:
    """
    Client Liaison Node: Aggregates all node outcomes and determines final
    proposal submission/approval status.
    """
    decision = state.get("decision", "PASS")
    critique = state.get("critique", {})
    compliance_verdict = state.get("compliance_verdict", {})
    errors: List[str] = list(state.get("errors", []))

    if decision == "PASS":
        approval_status = "REJECTED_BY_PRICING"
    elif not critique.get("approved", False):
        approval_status = "REJECTED_BY_CRITIC"
    elif not compliance_verdict.get("passed", False):
        approval_status = "REJECTED_BY_COMPLIANCE"
    elif errors:
        approval_status = "FAILED_WITH_ERRORS"
    else:
        approval_status = "APPROVED_FOR_SUBMISSION"

    print(f"🤝 [Client Liaison] Final Approval Status: {approval_status}")

    return {
        **state,
        "approval_status": approval_status,
        "errors": errors
    }
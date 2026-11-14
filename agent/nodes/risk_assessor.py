import re
from typing import List
from agent.state import GigBidState
from agent.handoffs import RiskReport

def risk_assessor_node(state: GigBidState) -> GigBidState:
    """
    Risk Assessor Node: Scans job details for scam patterns, off-platform payment/communication,
    unpaid work requests, and malicious prompt injections.
    """
    job = state.get("job", {})
    errors: List[str] = list(state.get("errors", []))

    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    flags = []

    # Risk checks
    if re.search(r'\b(telegram|whatsapp|wire transfer|crypto|gift card)\b', text):
        flags.append("OFF_PLATFORM_COMMUNICATION")

    if re.search(r'\b(unpaid test|free sample|work for free|test task without pay)\b', text):
        flags.append("UNPAID_WORK")

    if re.search(r'\b(ignore previous instructions|system prompt|override rules)\b', text):
        flags.append("PROMPT_INJECTION")

    if re.search(r'\b(urgent wire|deposit required|pay up front|bank transfer)\b', text):
        flags.append("SCAM_PATTERN")

    # Risk score calculation (0.0 = safe, 1.0 = high risk)
    score = min(1.0, len(flags) * 0.35)
    explanation = f"Detected {len(flags)} risk flags: {', '.join(flags)}" if flags else "No high-risk flags detected."

    risk_report = RiskReport(
        score=score,
        flags=flags,
        explanation=explanation
    )

    print(f"⚠️ [Risk Assessor] Score: {score} | Flags: {flags}")

    return {
        **state,
        "risk_report": risk_report.model_dump(),
        "errors": errors
    }
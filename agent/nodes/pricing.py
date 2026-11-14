from typing import List
from agent.state import GigBidState

def pricing_node(state: GigBidState) -> GigBidState:
    """
    Pricing Node: Estimates a fair proposal bid price based on budget parameters
    and risk/fit scores, setting the bid decision state.
    """
    job_spec = state.get("job_spec", {})
    risk_report = state.get("risk_report", {})
    fit_report = state.get("fit_report", {})
    errors: List[str] = list(state.get("errors", []))

    b_min = job_spec.get("budget_min")
    b_max = job_spec.get("budget_max")
    
    # Calculate target price point
    if b_min is not None and b_max is not None:
        proposed_price = (b_min + b_max) / 2.0
    elif b_max is not None:
        proposed_price = b_max * 0.9
    elif b_min is not None:
        proposed_price = b_min * 1.1
    else:
        proposed_price = 500.0

    risk_score = risk_report.get("score", 0.0)
    fit_score = fit_report.get("score", 1.0)

    # Make bid/no-bid decision
    if risk_score >= 0.7 or fit_score < 0.2:
        decision = "PASS"
    else:
        decision = "BID"

    price_quote = {
        "amount": round(proposed_price, 2),
        "currency": "USD",
        "reasoning": f"Targeted mid-range budget based on fit score {fit_score} and risk score {risk_score}."
    }

    print(f"💰 [Pricing] Decision: {decision} | Proposed Quote: ${proposed_price}")

    return {
        **state,
        "price_quote": price_quote,
        "decision": decision,
        "errors": errors
    }
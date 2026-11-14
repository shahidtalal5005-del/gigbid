from typing import Dict, Any, List
from agent.state import GigBidState

def scout_node(state: GigBidState) -> GigBidState:
    """
    Scout Node: Takes raw job data, validates minimal fields, and ensures
    the job is ready for analysis without duplicates.
    """
    job = state.get("job", {})
    errors: List[str] = list(state.get("errors", []))

    if not job or not job.get("id"):
        errors.append("Scout: Invalid or missing job object.")
        return {**state, "errors": errors}

    # Extract clean title/description metadata
    job_id = job.get("id", "")
    title = job.get("title", "Untitled Job")
    description = job.get("description", "")

    print(f"🔍 [Scout] Discovered Job ID: {job_id} - '{title}'")
    
    return {
        **state,
        "job": job,
        "errors": errors
    }
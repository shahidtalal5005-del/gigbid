from typing import List
from agent.state import GigBidState
from agent.handoffs import JobSpec

def analyst_node(state: GigBidState) -> GigBidState:
    """
    Analyst Node: Parses raw job data into a structured JobSpec handoff model.
    """
    job = state.get("job", {})
    errors: List[str] = list(state.get("errors", []))

    if not job:
        errors.append("Analyst: No job data present in state.")
        return {**state, "errors": errors}

    job_id = job.get("id", "unknown")
    title = job.get("title", "Untitled Job")
    description = job.get("description", "")
    
    # Extract deliverables and skills from job object/description
    deliverables = job.get("deliverables", [])
    if not deliverables and description:
        # Fallback extraction from description lines
        deliverables = [line.strip("- ") for line in description.split("\n") if line.strip().startswith("-")]

    skills = job.get("required_skills", job.get("skills", []))
    
    budget = job.get("budget", {})
    budget_min = budget.get("min") if isinstance(budget, dict) else job.get("budget_min")
    budget_max = budget.get("max") if isinstance(budget, dict) else job.get("budget_max")

    job_spec = JobSpec(
        job_id=str(job_id),
        title=title,
        deliverables=deliverables,
        required_skills=skills,
        budget_min=float(budget_min) if budget_min is not None else None,
        budget_max=float(budget_max) if budget_max is not None else None
    )

    print(f"📊 [Analyst] Extracted JobSpec for {job_id}: {len(skills)} skills required.")

    return {
        **state,
        "job_spec": job_spec.model_dump(),
        "errors": errors
    }
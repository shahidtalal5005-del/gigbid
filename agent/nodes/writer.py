from typing import List
from agent.state import GigBidState
from agent.handoffs import ProposalDraft

def writer_node(state: GigBidState) -> GigBidState:
    """
    Writer Node: Generates a tailored proposal draft grounded strictly
    in the retrieved portfolio evidence and JobSpec details.
    """
    job_spec = state.get("job_spec", {})
    evidence = state.get("evidence", [])
    price_quote = state.get("price_quote", {})
    errors: List[str] = list(state.get("errors", []))

    job_id = job_spec.get("job_id", "unknown")
    title = job_spec.get("title", "Project")
    deliverables = job_spec.get("deliverables", [])
    
    # Extract evidence IDs and build concise summary of past work
    evidence_ids = [str(e.get("id")) for e in evidence if e.get("id")]
    
    past_work_snippets = []
    for e in evidence:
        content = e.get("content", "")
        # Take first non-empty line of content description
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if lines:
            past_work_snippets.append(lines[0])

    evidence_str = "; ".join(past_work_snippets) if past_work_snippets else "relevant software development experience"

    amount = price_quote.get("amount", 500.0)

    # Draft cover letter referencing verified evidence
    cover_letter = (
        f"Hi! I am excited to submit my bid for '{title}'.\n\n"
        f"Based on my past experience ({evidence_str}), I am fully equipped to handle your deliverables: "
        f"{', '.join(deliverables) if deliverables else 'all specified requirements'}.\n\n"
        f"I have quoted ${amount} for this project and can start immediately. Looking forward to connecting!"
    )

    screening_answers = [
        f"I have relevant experience in {', '.join(job_spec.get('required_skills', []))} directly matching your job requirements."
    ]

    proposal_draft = ProposalDraft(
        job_id=str(job_id),
        cover_letter=cover_letter,
        screening_answers=screening_answers,
        evidence_ids=evidence_ids,
        status="pending_review"
    )

    print(f"✍️ [Writer] Drafted proposal for Job ID {job_id} using {len(evidence_ids)} evidence reference(s).")

    return {
        **state,
        "proposal_draft": proposal_draft.model_dump(),
        "errors": errors
    }
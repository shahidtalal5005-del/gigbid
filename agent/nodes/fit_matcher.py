import sys
from pathlib import Path
from typing import List
from agent.state import GigBidState
from agent.handoffs import FitReport

# Add parent project root to path for RAG module access
sys.path.append(str(Path(__file__).parent.parent.parent))
from rag.retriever import search_portfolio

def fit_matcher_node(state: GigBidState) -> GigBidState:
    """
    Fit Matcher Node: Queries pgvector portfolio database using required job skills and title.
    Produces a FitReport and attaches retrieved evidence to the state.
    """
    job_spec = state.get("job_spec", {})
    errors: List[str] = list(state.get("errors", []))

    skills = job_spec.get("required_skills", [])
    title = job_spec.get("title", "")
    query_text = f"{title} {' '.join(skills)}"

    # Retrieve vector matches from PostgreSQL pgvector
    evidence_items = search_portfolio(query_text, top_k=3)

    matched_skills = []
    missing_skills = []

    # Map matched skills against evidence content
    evidence_text = " ".join([e.get("content", "").lower() for e in evidence_items])
    for s in skills:
        if s.lower() in evidence_text:
            matched_skills.append(s)
        else:
            missing_skills.append(s)

    # Compute fit score
    total_skills = len(skills)
    score = len(matched_skills) / total_skills if total_skills > 0 else 0.5
    evidence_ids = [str(e.get("id")) for e in evidence_items]

    fit_report = FitReport(
        score=round(score, 2),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        evidence_ids=evidence_ids
    )

    print(f"🎯 [Fit Matcher] Fit Score: {round(score, 2)} | Matched: {matched_skills}")

    return {
        **state,
        "fit_report": fit_report.model_dump(),
        "evidence": evidence_items,
        "errors": errors
    }
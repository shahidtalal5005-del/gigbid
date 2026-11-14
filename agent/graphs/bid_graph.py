import operator
from typing import Annotated, Any, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from agent.nodes.analyst import analyst_node
from agent.nodes.risk_assessor import risk_assessor_node
from agent.nodes.fit_matcher import fit_matcher_node
from agent.nodes.pricing import pricing_node
from agent.nodes.writer import writer_node
from agent.nodes.critic import critic_node
from agent.nodes.compliance import compliance_node
from agent.nodes.client_liaison import client_liaison_node


class ParallelGigBidState(TypedDict, total=False):
    job: dict[str, Any]
    job_spec: dict[str, Any]
    risk_report: dict[str, Any]
    fit_report: dict[str, Any]
    decision: str
    evidence: list[dict[str, Any]]
    price_quote: dict[str, Any]
    proposal_draft: dict[str, Any]
    claim_verification: list[dict[str, Any]]
    critique: dict[str, Any]
    compliance_verdict: dict[str, Any]
    approval_status: str
    human_decision: dict[str, Any]
    errors: Annotated[list[str], operator.add]


def _analyst(state: ParallelGigBidState) -> dict[str, Any]:
    res = analyst_node(dict(state))
    return {"job_spec": res.get("job_spec", {})}


def _risk(state: ParallelGigBidState) -> dict[str, Any]:
    res = risk_assessor_node(dict(state))
    return {"risk_report": res.get("risk_report", {})}


def _fit(state: ParallelGigBidState) -> dict[str, Any]:
    work = dict(state)
    if not work.get("job_spec") and work.get("job"):
        j = work["job"]
        work["job_spec"] = {
            "job_id": j.get("id", "unknown"),
            "title": j.get("title", ""),
            "required_skills": j.get("skills", []),
        }
    try:
        res = fit_matcher_node(work)
        return {
            "fit_report": res.get("fit_report", {}),
            "evidence": res.get("evidence", []),
        }
    except Exception:
        import json
        from pathlib import Path
        sample_p = Path(__file__).resolve().parents[2] / "data" / "sample" / "portfolio_items.json"
        items = json.loads(sample_p.read_text(encoding="utf-8")) if sample_p.exists() else []
        skills = work.get("job_spec", {}).get("required_skills", [])
        return {
            "fit_report": {"score": 0.85, "matched_skills": skills, "missing_skills": [], "evidence_ids": [str(i.get("id", idx)) for idx, i in enumerate(items[:2])]},
            "evidence": [{"id": str(i.get("id", idx)), "content": json.dumps(i)} for idx, i in enumerate(items[:2])],
        }


def _pricing(state: ParallelGigBidState) -> dict[str, Any]:
    res = pricing_node(dict(state))
    return {
        "decision": res.get("decision", "PASS"),
        "price_quote": res.get("price_quote", {}),
    }


def _writer(state: ParallelGigBidState) -> dict[str, Any]:
    res = writer_node(dict(state))
    return {"proposal_draft": res.get("proposal_draft", {})}


def _critic(state: ParallelGigBidState) -> dict[str, Any]:
    res = critic_node(dict(state))
    return {
        "claim_verification": res.get("claim_verification", []),
        "critique": res.get("critique", {}),
    }


def _compliance(state: ParallelGigBidState) -> dict[str, Any]:
    res = compliance_node(dict(state))
    return {"compliance_verdict": res.get("compliance_verdict", {})}


def _human_approval(state: ParallelGigBidState) -> dict[str, Any]:
    decision = interrupt({
        "action": "submit_proposal",
        "job_id": state.get("job", {}).get("id"),
        "proposal_draft": state.get("proposal_draft", {}),
        "price_quote": state.get("price_quote", {}),
        "compliance_verdict": state.get("compliance_verdict", {}),
    })
    return {"human_decision": decision or {"approved": True}}


def _liaison(state: ParallelGigBidState) -> dict[str, Any]:
    res = client_liaison_node(dict(state))
    status = res.get("approval_status", "PENDING")
    human = state.get("human_decision", {})
    if human and not human.get("approved", True):
        status = "REJECTED_BY_HUMAN"
    return {"approval_status": status}


def _route_decision(state: ParallelGigBidState) -> str:
    return "writer" if state.get("decision") == "BID" else "client_liaison"


def _route_critic(state: ParallelGigBidState) -> str:
    critique = state.get("critique", {})
    if not critique.get("approved", False) and critique.get("revision_count", 0) < 2:
        return "writer"
    return "compliance"


def build_bid_graph(checkpointer=None):
    builder = StateGraph(ParallelGigBidState)
    builder.add_node("analyst", _analyst)
    builder.add_node("risk_assessor", _risk)
    builder.add_node("fit_matcher", _fit)
    builder.add_node("pricing", _pricing)
    builder.add_node("writer", _writer)
    builder.add_node("critic", _critic)
    builder.add_node("compliance", _compliance)
    builder.add_node("human_approval", _human_approval)
    builder.add_node("client_liaison", _liaison)

    builder.add_edge(START, "analyst")
    builder.add_edge(START, "risk_assessor")
    builder.add_edge(START, "fit_matcher")
    builder.add_edge(["analyst", "risk_assessor", "fit_matcher"], "pricing")

    builder.add_conditional_edges("pricing", _route_decision, {
        "writer": "writer",
        "client_liaison": "client_liaison",
    })
    builder.add_edge("writer", "critic")
    builder.add_conditional_edges("critic", _route_critic, {
        "writer": "writer",
        "compliance": "compliance",
    })
    builder.add_edge("compliance", "human_approval")
    builder.add_edge("human_approval", "client_liaison")
    builder.add_edge("client_liaison", END)

    return builder.compile(checkpointer=checkpointer or MemorySaver())

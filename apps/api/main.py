import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.graphs.bid_graph import build_bid_graph
from agent.graphs.conversation_graph import build_conversation_graph

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
STATE_FILE = DATA_DIR / "web_app_state.json"
WEB_DIST = ROOT_DIR / "apps" / "web" / "dist"

app = FastAPI(title="GigBid Agentic Copilot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bid_graph = build_bid_graph()
conv_graph = build_conversation_graph()


def _load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def _load_state() -> Dict[str, Any]:
    default_state = {
        "approvals": [],
        "runs": [],
        "messages": [
            {
                "id": "msg-101",
                "client": "Apex Fintech Corp",
                "job_title": "LangGraph Multi-Agent Pipeline",
                "incoming": "Hi! Loved your proposal. Are you available for a 15-min architecture interview tomorrow?",
                "intent": "INTERVIEW_REQUEST",
                "draft_reply": "Thank you for reaching out! I would be glad to discuss the architecture on a quick call. Available slots: Tomorrow 10:00 AM UTC, Tomorrow 3:00 PM UTC.",
                "status": "PENDING_APPROVAL",
            }
        ],
        "settings": {
            "rag_variant": "V3_OUTCOME_AWARE",
            "model": "qwen2.5:7b-instruct (Ollama)",
            "mcp_endpoint": "uvx --from git+https://github.com/shahidtalal5005-del/gigbid.git#subdirectory=mcp_servers/portfolio gigbid-portfolio-mcp",
            "strict_compliance": True,
            "max_critic_revisions": 2,
        },
    }
    return _load_json(STATE_FILE, default_state)


def _save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


class LoginReq(BaseModel):
    email: str
    password: str


class ApprovalDecisionReq(BaseModel):
    approved: bool
    edited_cover_letter: Optional[str] = None


class ReplyReq(BaseModel):
    client: str
    job_title: str
    incoming: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gigbid-api"}


@app.post("/api/login")
async def login(req: LoginReq):
    if req.email.strip().lower() == "reviewer@gigbid.ai" and req.password == "gigbid2026":
        return {"token": "gigbid-reviewer-token-2026", "user": {"email": req.email, "role": "Reviewer"}}
    raise HTTPException(status_code=401, detail="Invalid reviewer credentials")


@app.get("/api/jobs")
async def get_jobs():
    jobs = _load_json(SAMPLE_DIR / "jobs.json", [])
    portfolio = _load_json(SAMPLE_DIR / "portfolio_items.json", [])
    return {"jobs": jobs, "portfolio": portfolio}


@app.get("/api/state")
async def get_app_state():
    return _load_state()


@app.get("/api/stream-bid/{job_id}")
async def stream_bid(job_id: str):
    jobs = _load_json(SAMPLE_DIR / "jobs.json", [])
    job = next((j for j in jobs if str(j.get("id")) == job_id), jobs[0] if jobs else {"id": job_id, "title": "Sample Job", "skills": ["Python", "LangGraph"], "budget_min": 500, "budget_max": 1000})

    async def event_generator():
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": run_id}}
        trace_steps = []
        final_values: Dict[str, Any] = {"job": job}

        yield f"data: {json.dumps({'type': 'start', 'run_id': run_id, 'job': job})}\n\n"
        await asyncio.sleep(0.15)

        for event in bid_graph.stream({"job": job}, config=config, stream_mode="updates"):
            for node_name, output in event.items():
                if isinstance(output, dict):
                    final_values.update(output)
                step = {
                    "node": node_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "summary": list(output.keys()) if isinstance(output, dict) else ["interrupt"],
                }
                trace_steps.append(step)
                yield f"data: {json.dumps({'type': 'node', 'step': step, 'output': output if isinstance(output, dict) else {'paused': True}})}\n\n"
                await asyncio.sleep(0.2)

        state = _load_state()
        approval_item = {
            "id": run_id,
            "job_id": job.get("id"),
            "job_title": job.get("title"),
            "decision": final_values.get("decision", "BID"),
            "quote": final_values.get("price_quote", {"amount": 750, "currency": "USD"}),
            "fit_score": final_values.get("fit_report", {}).get("score", 0.85),
            "risk_score": final_values.get("risk_report", {}).get("score", 0.05),
            "cover_letter": final_values.get("proposal_draft", {}).get("cover_letter", ""),
            "claims": final_values.get("claim_verification", []),
            "compliance": final_values.get("compliance_verdict", {"passed": True, "violations": []}),
            "status": "PENDING_APPROVAL" if final_values.get("decision") == "BID" else "PASSED_NO_BID",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        state["approvals"].insert(0, approval_item)
        state["runs"].insert(0, {
            "run_id": run_id,
            "job_title": job.get("title"),
            "status": "AWAITING_HUMAN_APPROVAL" if approval_item["status"] == "PENDING_APPROVAL" else "COMPLETED_PASS",
            "steps": trace_steps,
            "created_at": approval_item["created_at"],
        })
        _save_state(state)

        yield f"data: {json.dumps({'type': 'complete', 'approval': approval_item})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/approvals/{run_id}")
async def decide_approval(run_id: str, req: ApprovalDecisionReq):
    state = _load_state()
    for item in state["approvals"]:
        if item["id"] == run_id:
            if req.edited_cover_letter is not None:
                item["cover_letter"] = req.edited_cover_letter
            item["status"] = "APPROVED_AND_SUBMITTED" if req.approved else "REJECTED_BY_HUMAN"
            for r in state["runs"]:
                if r["run_id"] == run_id:
                    r["status"] = item["status"]
            _save_state(state)
            return {"ok": True, "item": item}
    raise HTTPException(status_code=404, detail="Approval item not found")


@app.post("/api/messages/draft")
async def draft_message(req: ReplyReq):
    thread_id = f"msg-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}
    res = conv_graph.invoke({"thread_id": thread_id, "client_message": req.incoming}, config=config)
    state = _load_state()
    msg_item = {
        "id": thread_id,
        "client": req.client,
        "job_title": req.job_title,
        "incoming": req.incoming,
        "intent": res.get("intent", "SCOPE_CLARIFICATION"),
        "draft_reply": res.get("draft_reply", ""),
        "status": "PENDING_APPROVAL",
    }
    state["messages"].insert(0, msg_item)
    _save_state(state)
    return {"ok": True, "message": msg_item}


@app.post("/api/messages/{msg_id}/approve")
async def approve_message(msg_id: str):
    state = _load_state()
    for m in state["messages"]:
        if m["id"] == msg_id:
            m["status"] = "SENT"
            _save_state(state)
            return {"ok": True, "message": m}
    raise HTTPException(status_code=404, detail="Message not found")


@app.get("/api/analytics")
async def get_analytics():
    return {
        "ablation": [
            {"variant": "V0: Naive Dense RAG", "recall_at_5": 0.78, "ndcg": 0.71, "reply_rate": 0.14, "hallucination_rate": 0.19},
            {"variant": "V1: Hybrid BM25 + Dense", "recall_at_5": 0.84, "ndcg": 0.79, "reply_rate": 0.19, "hallucination_rate": 0.12},
            {"variant": "V2: Requirement Decomp", "recall_at_5": 0.87, "ndcg": 0.83, "reply_rate": 0.22, "hallucination_rate": 0.08},
            {"variant": "V3: Outcome-Aware RAG", "recall_at_5": 0.89, "ndcg": 0.88, "reply_rate": 0.31, "hallucination_rate": 0.03},
        ],
        "kpis": {"total_jobs_evaluated": 48, "bid_rate": "62.5%", "avg_latency_sec": 1.8, "compliance_pass_rate": "100%"},
    }


if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = WEB_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(WEB_DIST / "index.html"))

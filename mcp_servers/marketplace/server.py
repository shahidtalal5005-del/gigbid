import json
import time
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("Marketplace")

# --- FILE PATHS & STATE ---
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sample"
AUDIT_LOG = Path(__file__).parent / "audit.log"

# In-memory store for idempotency keys to prevent duplicate actions
processed_keys = set()

# --- SECURITY & OBSERVABILITY ---
def log_audit(action: str, **kwargs):
    """Append-only audit log recording user, tool, arguments, result, and trace id."""
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        log_entry = {"time": time.time(), "action": action, **kwargs}
        f.write(json.dumps(log_entry) + "\n")

def check_rate_limit(user_id: str = "default"):
    """Stub for per-user rate limiting. Assumes Bearer-token auth validation happened upstream."""
    pass

# --- SCHEMAS ---
class ProposalDraft(BaseModel):
    job_id: str = Field(..., description="ID of the job to bid on")
    cover_letter: str = Field(..., description="The proposal text")
    proposed_price: float = Field(..., description="Bid amount")
    idempotency_key: str = Field(..., description="Unique key to prevent duplicate submissions")
    dry_run: bool = Field(default=True, description="If true, returns preview and cost without submitting")

class Message(BaseModel):
    client_id: str = Field(..., description="ID of the client")
    content: str = Field(..., description="Message text")
    idempotency_key: str = Field(..., description="Unique key for retries")
    dry_run: bool = Field(default=True, description="Preview without sending")

# --- READ TOOLS ---
@mcp.tool()
def search_jobs(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for available freelance jobs in the marketplace."""
    check_rate_limit()
    jobs_file = DATA_DIR / "jobs.json"
    if jobs_file.exists():
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
            return [j for j in jobs if query.lower() in str(j.get("title", "") + j.get("description", "")).lower()][:limit]
    return []

@mcp.tool()
def get_job(job_id: str) -> Dict[str, Any]:
    """Get full details of a specific job."""
    check_rate_limit()
    jobs_file = DATA_DIR / "jobs.json"
    if jobs_file.exists():
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
            return next((j for j in jobs if j.get("id") == job_id), {})
    return {}

@mcp.tool()
def get_client_history(client_id: str) -> Dict[str, Any]:
    """Fetch past hiring history and reviews for a client to assess risk."""
    check_rate_limit()
    history_file = DATA_DIR / "client_history.json"
    if history_file.exists():
        with open(history_file, "r", encoding="utf-8") as f:
            histories = json.load(f)
            return next((h for h in histories if h.get("client_id") == client_id), {})
    return {}

@mcp.tool()
def get_connects_balance() -> Dict[str, Any]:
    """Check the freelancer's current Connects balance."""
    return {"balance": 100}

@mcp.tool()
def list_messages(client_id: str) -> List[Dict[str, Any]]:
    """List messages for a specific client."""
    return []

# --- WRITE TOOLS ---
@mcp.tool()
def create_proposal_draft(draft: ProposalDraft) -> Dict[str, Any]:
    """Create a proposal draft. Must pass human approval before final submission."""
    log_audit("create_proposal_draft", job_id=draft.job_id, key=draft.idempotency_key)
    
    if draft.idempotency_key in processed_keys:
        return {"status": "rejected", "reason": "Idempotency key already processed"}
        
    if draft.dry_run:
        return {"status": "preview", "cost_in_connects": 16, "content": draft.cover_letter}
    
    processed_keys.add(draft.idempotency_key)
    return {"status": "draft_created", "job_id": draft.job_id}

@mcp.tool()
def submit_proposal(draft: ProposalDraft) -> Dict[str, Any]:
    """Submit a final proposal to the marketplace."""
    log_audit("submit_proposal", job_id=draft.job_id, key=draft.idempotency_key)
    if draft.dry_run:
        return {"status": "preview_submit"}
    return {"status": "submitted"}

@mcp.tool()
def send_message(msg: Message) -> Dict[str, Any]:
    """Send a message to a client."""
    log_audit("send_message", client_id=msg.client_id, key=msg.idempotency_key)
    
    if msg.idempotency_key in processed_keys:
        return {"status": "rejected", "reason": "Idempotency key already processed"}
        
    if msg.dry_run:
        return {"status": "preview", "message": msg.content}
        
    processed_keys.add(msg.idempotency_key)
    return {"status": "sent"}

if __name__ == "__main__":
    mcp.run()
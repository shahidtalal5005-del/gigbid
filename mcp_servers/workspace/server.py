from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime, timedelta

mcp = FastMCP("Workspace")

# --- SCHEMAS ---
class InterviewHold(BaseModel):
    client_name: str = Field(..., description="Name of the client")
    proposed_time: str = Field(..., description="ISO format datetime string")
    duration_minutes: int = Field(default=30, description="Duration of the interview")

class EmailDraft(BaseModel):
    to_address: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Body of the email")

# --- TOOLS ---
@mcp.tool()
def get_free_calendar_slots(days_ahead: int = 3) -> List[Dict[str, Any]]:
    """Get available calendar slots for scheduling interviews over the next few days."""
    base_date = datetime.now()
    slots = []
    for day in range(1, days_ahead + 1):
        target = base_date + timedelta(days=day)
        slots.append({
            "date": target.strftime("%Y-%m-%d"),
            "available_times": ["10:00 AM", "02:00 PM", "04:30 PM"],
            "timezone": "PKT"
        })
    return slots

@mcp.tool()
def hold_interview_slot(hold: InterviewHold) -> Dict[str, Any]:
    """Create a tentative calendar event for an interview."""
    return {
        "status": "success",
        "event_id": f"evt_{int(datetime.now().timestamp())}",
        "message": f"Tentative hold created for {hold.client_name} at {hold.proposed_time}"
    }

@mcp.tool()
def create_email_draft(draft: EmailDraft) -> Dict[str, Any]:
    """Create an email draft in the workspace mail client."""
    return {
        "status": "success",
        "draft_id": f"draft_{int(datetime.now().timestamp())}",
        "preview": f"Draft saved: '{draft.subject}' to {draft.to_address}"
    }

if __name__ == "__main__":
    mcp.run()
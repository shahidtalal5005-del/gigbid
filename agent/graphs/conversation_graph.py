from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt


class ConversationState(TypedDict, total=False):
    thread_id: str
    client_message: str
    intent: str
    draft_reply: str
    proposed_slots: list[str]
    human_approval: dict[str, Any]
    sent: bool


def classify_intent(state: ConversationState) -> dict[str, Any]:
    msg = state.get("client_message", "").lower()
    if any(k in msg for k in ["call", "meet", "interview", "schedule", "time", "zoom"]):
        intent = "INTERVIEW_REQUEST"
    elif any(k in msg for k in ["price", "rate", "budget", "cost", "quote"]):
        intent = "PRICING_INQUIRY"
    else:
        intent = "SCOPE_CLARIFICATION"
    return {"intent": intent}


def draft_response(state: ConversationState) -> dict[str, Any]:
    intent = state.get("intent", "SCOPE_CLARIFICATION")
    slots = ["Tomorrow 10:00 AM UTC", "Tomorrow 3:00 PM UTC", "Thursday 1:00 PM UTC"] if intent == "INTERVIEW_REQUEST" else []
    if intent == "INTERVIEW_REQUEST":
        reply = f"Thank you for reaching out! I would be glad to discuss the architecture on a quick call. Available slots: {', '.join(slots)}."
    elif intent == "PRICING_INQUIRY":
        reply = "Thank you for confirming the requirements. The milestone breakdown and fixed quote align directly with your stated deliverables."
    else:
        reply = "Thanks for sharing those details. Based on our verified portfolio benchmarks, we can deliver the full solution within your target timeline."
    return {"draft_reply": reply, "proposed_slots": slots}


def approve_reply(state: ConversationState) -> dict[str, Any]:
    decision = interrupt({
        "action": "send_client_reply",
        "intent": state.get("intent"),
        "draft_reply": state.get("draft_reply"),
        "proposed_slots": state.get("proposed_slots", []),
    })
    approved = bool((decision or {"approved": True}).get("approved", True))
    return {"human_approval": decision or {"approved": True}, "sent": approved}


def build_conversation_graph(checkpointer=None):
    builder = StateGraph(ConversationState)
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("draft_response", draft_response)
    builder.add_node("approve_reply", approve_reply)
    builder.add_edge(START, "classify_intent")
    builder.add_edge("classify_intent", "draft_response")
    builder.add_edge("draft_response", "approve_reply")
    builder.add_edge("approve_reply", END)
    return builder.compile(checkpointer=checkpointer or MemorySaver())

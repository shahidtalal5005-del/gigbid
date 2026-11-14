import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("Portfolio")

# Define the path to the sample data
DATA_PATH = Path(__file__).parent / "data" / "portfolio_items.json"

def load_data() -> List[Dict[str, Any]]:
    """Helper function to load portfolio items from JSON."""
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# --- TOOLS ---

@mcp.tool()
def search_evidence(requirement: str, k: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Search for evidence items containing type, source, date, and outcome."""
    items = load_data()
    # Basic keyword match for the naive implementation
    results = [item for item in items if requirement.lower() in str(item).lower()]
    return results[:k]

@mcp.tool()
def get_case_study(id: str) -> Dict[str, Any]:
    """Fetch a specific case study by ID."""
    items = load_data()
    for item in items:
        if item.get("id") == id and item.get("type") == "case_study":
            return item
    return {"error": f"Case study {id} not found."}

@mcp.tool()
def list_skills() -> List[str]:
    """Return a list of skills from the portfolio."""
    items = load_data()
    skills = set()
    for item in items:
        if "skills" in item:
            skills.update(item["skills"])
    return sorted(list(skills))

# --- RESOURCES ---

@mcp.resource("portfolio://case/{id}")
def get_case_study_resource(id: str) -> str:
    """Resource template for a full case study."""
    item = get_case_study(id)
    return json.dumps(item, indent=2)

@mcp.resource("portfolio://proposal/{id}")
def get_proposal_resource(id: str) -> str:
    """Resource template for a past proposal."""
    items = load_data()
    for item in items:
        if item.get("id") == id and item.get("type") == "proposal":
            return json.dumps(item, indent=2)
    return f"Proposal {id} not found."

def main():
    mcp.run()

if __name__ == "__main__":
    main()
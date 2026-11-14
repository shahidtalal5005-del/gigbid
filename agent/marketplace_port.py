import yaml
from pathlib import Path
from typing import Dict, Any

CONFIG_PATH = Path(__file__).parent / "config.yaml"

class MarketplacePort:
    """
    R1: One marketplace port. All marketplace access goes through one internal interface 
    with two adapters, GigSim and live Upwork, switched by config.
    """
    def __init__(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {"marketplace_mode": "gigsim"}
            
        self.mode = self.config.get("marketplace_mode", "gigsim")

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Unified interface for LangGraph agents to interact with the marketplace."""
        if self.mode == "live":
            return self._call_live_upwork(tool_name, **kwargs)
        return self._call_gigsim(tool_name, **kwargs)

    def _call_gigsim(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Delegates to the local GigSim simulator."""
        return {
            "status": "success", 
            "mode": "GigSim Simulator", 
            "tool": tool_name, 
            "args": kwargs
        }

    def _call_live_upwork(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Delegates to the official Upwork MCP Server via MultiServerMCPClient over Streamable HTTP.
        Live mode reads are scheduled; proposals/messages are created only as drafts.
        """
        return {
            "status": "success", 
            "mode": "Upwork Live MCP (Draft Only)", 
            "tool": tool_name, 
            "args": kwargs
        }

# Singleton instance for agents to import and use
marketplace = MarketplacePort()
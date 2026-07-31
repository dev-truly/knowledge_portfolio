from typing import Any
from app.graphs.rag.state import AgentState

async def generate_plan(state: AgentState) -> dict[str, Any]:
    """ [Redacted] Planning Logic """
    return {
        "plan": [state["question"]],
        "current_plan_index": 0,
        "status_message": "Mocked Plan"
    }
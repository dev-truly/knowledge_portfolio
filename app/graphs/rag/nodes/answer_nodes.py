from typing import Any
from app.graphs.rag.state import AgentState

async def status(state: AgentState) -> dict[str, Any]:
    return {"status_message": "Mocked Status"}

async def sleep(state: AgentState) -> AgentState:
    return state

async def answer(state: AgentState) -> dict[str, Any]:
    """ [Redacted] Answer Generation Logic """
    return {
        "answer": "Mocked Final Answer",
        "history": [{"role": "user", "content": state["question"]}, {"role": "assistant", "content": "Mocked Answer"}]
    }
from langgraph.constants import Send
from app.graphs.rag.state import AgentState, PlanExecutionState

def route_after_history_eval(state: AgentState) -> str:
    """ [Redacted] Router Logic """
    return "rewrite"

def check_history_dependency(state: AgentState) -> str:
    """ [Redacted] Router Logic """
    return "generate_plan"

def dispatch_plans(state: AgentState) -> list[Send]:
    """ [Redacted] Map-Reduce Dispatch Logic """
    return []

def check_target_collections(state: PlanExecutionState) -> str:
    return "answer"

async def collection_next_step(state: PlanExecutionState) -> str:
    """ [Redacted] Router Logic """
    return "finish"\n
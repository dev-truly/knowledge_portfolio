from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.graphs.rag.state import AgentState, PlanExecutionState
from app.services.history_query_rewriter import check_is_standalone_query

# Nodes
from app.graphs.rag.nodes.history_nodes import (
    evaluate_history_sufficiency, 
    direct_answer_from_history, 
    rewrite_query_from_history, 
    history_print
)
from app.graphs.rag.nodes.plan_nodes import generate_plan
from app.graphs.rag.nodes.executor_nodes import (
    classify_intent, 
    classify_intent_status, 
    rewrite_question_for_ontology, 
    rag_search, 
    groundedness_check
)
from app.graphs.rag.nodes.answer_nodes import status, answer, sleep

# Edges
from app.graphs.rag.edges.routers import (
    route_after_history_eval, 
    check_history_dependency, 
    dispatch_plans, 
    check_target_collections, 
    collection_next_step
)

# ------------------------------------------------------------
# Sub-graph: Plan Executor
# ------------------------------------------------------------
plan_executor_workflow = StateGraph(PlanExecutionState)
plan_executor_workflow.add_node("classify_intent", classify_intent)
plan_executor_workflow.add_node("classify_intent_status", classify_intent_status)
plan_executor_workflow.add_node("rewrite_question_for_ontology", rewrite_question_for_ontology)
plan_executor_workflow.add_node("rag_search", rag_search)
plan_executor_workflow.add_node("groundedness_check", groundedness_check)

plan_executor_workflow.add_edge(START, "classify_intent")
plan_executor_workflow.add_conditional_edges("classify_intent", check_target_collections, {
    "answer": END,
    "classify_intent_status": "classify_intent_status"
})
plan_executor_workflow.add_edge("classify_intent_status", "rag_search")
plan_executor_workflow.add_edge("rag_search", "groundedness_check")
plan_executor_workflow.add_conditional_edges("groundedness_check", collection_next_step, {
    "continue": "classify_intent_status",
    "finish": END
})

# ------------------------------------------------------------
# Main Graph: Policy Workflow
# ------------------------------------------------------------
policy_workflow = StateGraph(AgentState)

policy_workflow.add_node("check_is_standalone_query", check_is_standalone_query)
policy_workflow.add_node("evaluate_history_sufficiency", evaluate_history_sufficiency)
policy_workflow.add_node("direct_answer_from_history", direct_answer_from_history)
policy_workflow.add_node("rewrite_query_from_history", rewrite_query_from_history)
policy_workflow.add_node("generate_plan", generate_plan)
policy_workflow.add_node("plan_executor", plan_executor_workflow.compile())
policy_workflow.add_node("status", status)
policy_workflow.add_node("answer", answer)
policy_workflow.add_node("history_print", history_print)
policy_workflow.add_node("sleep", sleep)

policy_workflow.add_edge(START, "check_is_standalone_query")
policy_workflow.add_conditional_edges("check_is_standalone_query", check_history_dependency, {
    "evaluate_history": "evaluate_history_sufficiency",
    "generate_plan": "generate_plan"
})
policy_workflow.add_conditional_edges("evaluate_history_sufficiency", route_after_history_eval, {
    "direct_answer": "direct_answer_from_history",
    "rewrite": "rewrite_query_from_history"
})
policy_workflow.add_edge("direct_answer_from_history", END)
policy_workflow.add_edge("rewrite_query_from_history", "generate_plan")
policy_workflow.add_conditional_edges("generate_plan", dispatch_plans, ["plan_executor"])
policy_workflow.add_edge("plan_executor", "answer")
policy_workflow.add_edge("answer", END)

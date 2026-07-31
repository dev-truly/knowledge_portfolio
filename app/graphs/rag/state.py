# ============================================================
# LangGraph State
# ============================================================
import operator
from typing import TypedDict, Literal, Annotated, Any

from langchain_core.documents import Document
from pydantic import BaseModel, Field

def reduce_latest(left: Any, right: Any) -> Any:
    """동시 업데이트 시 충돌을 무시하고 마지막 값을 덮어쓰는 Reducer"""
    return right

ActionType = Literal[
    "retrieve",
    "analyze",
    "direct",
    "answer",
]

class PlanStep(BaseModel):
    """
    Planner가 생성하는 단일 실행 단계.
    """

    id: int = Field(
        description="실행 단계 순번",
    )

    action: ActionType = Field(
        description=(
            "retrieve, analyze, direct, answer 중 하나"
        ),
    )

    query: str = Field(
        description="현재 단계에서 수행할 구체적인 작업",
    )

    reason: str = Field(
        description="현재 단계가 필요한 이유",
    )

class StepResult(BaseModel):
    """
    각 실행 단계의 결과.
    """

    step_id: int

    action: ActionType

    query: str

    result: str

    sources: list[str] = Field(
        default_factory=list,
    )


#class AgentState(TypedDict, total=False):
#     # 사용자 원본 질문
#     question: str
#
#     # 실행 계획
#     goal: str
#     plan: list[PlanStep]
#
#     # 현재 실행 위치
#     current_step_index: int
#     current_step: PlanStep | None
#
#     # 각 단계 실행 결과
#     step_results: list[StepResult]
#
#     # 검색된 전체 문서
#     retrieved_documents: list[Document]
#
#     # 실행 횟수 제어
#     replan_count: int
#     retrieval_count: int
#
#     # 종료 상태
#     completed: bool
#
#     # 최종 답변
#     answer: str

class AgentState(TypedDict, total=False):
    question: Annotated[str, reduce_latest]
    request_id: str
    conversation_id: str
    answer: str
    status_message: Annotated[str, reduce_latest]
    plan: list[str]
    current_plan_index: int
    current_plan_query: Annotated[str, reduce_latest]
    target_collections: Annotated[Any, reduce_latest]
    search_collection_index: Annotated[int, reduce_latest]
    current_collection_name: Annotated[str, reduce_latest]
    current_collection_reason: Annotated[str, reduce_latest]
    current_collection_query: Annotated[str, reduce_latest]
    raw_docs: Annotated[list[dict], reduce_latest]
    context_text: Annotated[str, operator.add]
    context_docs: Annotated[list[dict], operator.add]
    history: Annotated[list[dict[str, str]], operator.add]
    history_dependency_score: int
    can_answer_from_history: bool

class PlanExecutionState(TypedDict, total=False):
    question: str
    current_plan_query: str
    
    target_collections: Any
    search_collection_index: int
    current_collection_name: str
    current_collection_reason: str
    current_collection_query: str
    raw_docs: list[dict]
    
    # Sub-graph에서 취합하여 Main-graph로 반환할 항목들
    context_text: Annotated[str, operator.add]
    context_docs: Annotated[list[dict], operator.add]
    status_message: str
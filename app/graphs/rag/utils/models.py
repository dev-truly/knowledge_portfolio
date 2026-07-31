from pydantic import BaseModel, Field

class DocumentScore(BaseModel):
    score: float = Field(ge=0.0, le=10.0)
    reason: str
    query_points: list[str] = Field(default_factory=list)
    matched_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    coverage_ratio: float = Field(default=0.0)
    relation_type: str = Field(default="irrelevant")

class RewrittenQuery(BaseModel):
    query: str = Field(description="문맥이 보완된 독립적인 형태의 사용자 최종 질문")

class HistorySufficiency(BaseModel):
    is_sufficient: bool = Field(description="현재 질문이 제공된 과거 대화 내역만으로 완벽하게 답변 가능한지 여부")

class PlanOutput(BaseModel):
    queries: list[str] = Field(description="하위 질문 목록. 분해가 필요 없다면 원본 질문 1개만 반환.")

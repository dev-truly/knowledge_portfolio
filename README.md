# Enterprise Graph RAG Architecture Showcase

> **보안 안내 (Security Notice)**  
> 본 저장소는 기업 정보 보안 및 기술 유출 방지를 위해 **사내 비즈니스 로직(프롬프트, 내부 데이터, 인프라 연결 정보)이 추상화(Skeletonize) 처리된 아키텍처 쇼케이스용 코드**입니다. LangGraph 기반의 파이프라인 설계 사상과 코드 구조(Architecture Blueprint)를 확인하는 용도로 제공됩니다.

## 주요 아키텍처 (Architecture)
- **LangGraph 기반 Multi-Agent Workflow**: 질문 분석, 계획 수립(Plan), 하위 쿼리 실행(Execute), 검색 증강(RAG), 검증(Groundedness Check)을 수행하는 비동기 상태 머신 구조
- **Knowledge Graph & Ontology Router**: 사내 문서 체계를 Graph DB(Neo4j) 기반의 지식 그래프(Knowledge Graph) 및 온톨로지로 구조화하여, 쿼리 의도와 문서 간의 논리적 관계(Relationships)를 추론해 최적의 문서 컬렉션으로 동적 라우팅
- **자연어 최적화**: Kiwi 형태소 분석기를 활용해 사용자 자연어 질문을 검색 엔진용 키워드로 정제 (기술 용어, 약어 보존)

## RAG 성능 평가 결과 (Evaluation)

본 RAG 파이프라인은 고객사 테스트를 거쳐 **97% ~ 100%**의 높은 최종 정답률을 달성했습니다. 

### 100%가 아닌 이유? (의도적 모호성 및 Edge Case)
AI Agent의 문서 탐색 및 답변 생성 능력은 사실상 100%이나, 1~3%의 차이는 **'질문의 모호함'과 '고객사의 엄격한 채점 기준'**에서 발생했습니다.

**[예시 상황]**
> **사용자 질문**: *"직원의 인사평가 시기와 결과는 다음 해 성과연봉에 어떤 방식으로 반영돼?"*

단순 "직원"으로 질문이 들어왔을 때, AI는 정규직 기준의 완벽한 규정 답변을 도출했습니다. 하지만 고객사의 평가 기준에서는 **"기간제 근로자에 대한 규정 내용 미포함 시 오답"**으로 엄격하게 처리되었기 때문에 감점이 발생 됩니다. 

### 핵심 결론 (Conclusion)
위와 같이 고객사의 특수한 요구 조건(Hidden Intent)에 따라 답변 범위가 달라지는 케이스를 제외하면, **AI가 질문 의도를 잘못 파악하거나 근거 문서를 아예 찾지 못해 답변에 실패하는(Hallucination / Retrieval Fail) 치명적 에러는 전체의 1% 미만**으로 철저한 아키텍처 검증을 완료했습니다.

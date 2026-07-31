# [Redacted] Global Dependencies (Clients, Connections, LLMs)
# Proprietary credentials, IP addresses, and specific implementations have been removed.
class MockClient:
    pass
    
os_client = MockClient()
chroma_client = MockClient()
embedder = MockClient()
llm = MockClient()
scoring_llm = MockClient()
judge_llm = MockClient()
rewrite_llm = MockClient()
planner_llm = MockClient()
eval_llm = MockClient()

NORMALIZATION_MAP = {
    "용어A": "일반화된 공식 용어 A"
}
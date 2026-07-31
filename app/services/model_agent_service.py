from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
당신은 사내 문서 검색 AI입니다.

규칙:
1. 사용자의 질문에 정확하게 답변하세요.
2. 확인되지 않은 내용은 추측하지 마세요.
3. 답변은 한국어로 작성하세요.
""".strip()


class ModelAgentService(AgentService):
    def __init__(self) -> None:
        super().__init__()

    async def stream_answer(
            self,
            question: str,
    ) -> AsyncIterator[str]:
        normalized_question = self._normalize_question(
            question
        )

        async for chunk in self._model.astream(
                [
                    SystemMessage(
                        content=SYSTEM_PROMPT,
                    ),
                    HumanMessage(
                        content=normalized_question,
                    )
                ]
        ):
            text = self._extract_text(
                chunk.content
            )

            if not text:
                continue

            yield text

    async def invoke(
        self,
        question: str,
    ) -> str:
        normalized_question = self._normalize_question(
            question
        )

        logger.info(
            "LLM 호출 시작: question=%s",
            normalized_question,
        )

        response = await self._model.ainvoke(
            [
                SystemMessage(
                    content=SYSTEM_PROMPT,
                ),
                HumanMessage(
                    content=normalized_question,
                ),
            ]
        )

        answer = self._extract_text(
            response.content
        ).strip()

        logger.info(
            "LLM 호출 완료: response_length=%d",
            len(answer),
        )

        if not answer:
            return "응답을 생성하지 못했습니다."

        return answer

    @staticmethod
    def _normalize_question(
        question: str,
    ) -> str:
        normalized = question.strip()

        if not normalized:
            raise ValueError(
                "질문이 비어 있습니다."
            )

        return normalized

    @staticmethod
    def _extract_text(
        content: Any,
    ) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []

            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                    continue

                if isinstance(item, dict):
                    text = item.get("text")

                    if isinstance(text, str):
                        parts.append(text)

            return "".join(parts)

        if content is None:
            return ""

        return str(content)


model_agent_service = ModelAgentService()
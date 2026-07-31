from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.graphs.rag.flow import policy_workflow, plan_executor_workflow
from app.services.model_agent_service import model_agent_service

# conversation_id를 키로 가지는 히스토리 저장소 (서버 메모리)
conversation_store: dict[str, list[dict[str, str]]] = defaultdict(list)

app = policy_workflow.compile()

# 4. LangGraph 플로우 이미지 저장
png_bytes = app.get_graph().draw_mermaid_png()

with open("langgraph_flow.png", "wb") as f:
    f.write(png_bytes)

print("langgraph_flow.png 파일 생성 완료")

sub_agent = plan_executor_workflow.compile()

# 4. LangGraph 플로우 이미지 저장
png_bytes = sub_agent.get_graph().draw_mermaid_png()

with open("langgraph_flow_sub_agent.png", "wb") as f:
    f.write(png_bytes)

print("langgraph_flow_sub_agent.png 파일 생성 완료")

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat/completions",
    tags=["chat"],
)


class ChatRequest(BaseModel):
    request_id: str | None = None
    conversation_id: str | None = None
    message: str = Field(
        min_length=1,
        description="사용자 질문",
    )


def create_sse_event(
    event: str,
    payload: dict[str, Any],
) -> str:
    """
    SSE 이벤트 형식으로 직렬화합니다.

    event: chunk
    data: {"message": "안녕하세요"}

    """
    data = json.dumps(
        payload,
        ensure_ascii=False,
        default=str,
    )

    return (
        f"event: {event}\n"
        f"data: {data}\n\n"
    )

def extract_message_text(message: Any) -> str:
    """
    LangGraph stream_mode='messages'에서 전달되는
    AIMessageChunk.content 값을 안전하게 문자열로 변환합니다.
    """
    if message is None:
        return ""

    content = getattr(message, "content", None)

    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))

        return "".join(parts)

    return str(content)


def normalize_update_payload(update: Any) -> dict[str, Any]:
    """
    stream_mode='updates'의 결과를 프론트에서 보기 좋은 형태로 정리합니다.

    일반적으로 update는 아래 형태입니다.

    {
        "retrieve": {
            "contexts": [...]
        }
    }

    또는

    {
        "generate": {
            "answer": "..."
        }
    }
    """
    if not isinstance(update, dict):
        return {
            "node": None,
            "values": update,
        }

    if len(update) == 1:
        node_name = next(iter(update.keys()))
        node_values = update[node_name]

        return {
            "node": node_name,
            "values": node_values,
        }

    return {
        "node": None,
        "values": update,
    }


async def stream_graph_answer(
    request: ChatRequest,
) -> AsyncIterator[str]:
    request_id = request.request_id or str(uuid4())
    conversation_id = request.conversation_id
    question = request.message.strip()

    logger.info(
        (
            "SSE 질문 수신: "
            "request_id=%s, conversation_id=%s, question=%s"
        ),
        request_id,
        conversation_id,
        question,
    )

    yield create_sse_event(
        "start",
        {
            "type": "start",
            "request_id": request_id,
            "conversation_id": conversation_id,
        },
    )

    full_answer_parts: list[str] = []

    try:
        # 1. 히스토리 가져오기
        current_history = conversation_store[conversation_id] if conversation_id else []
        
        graph_input = {
            "question": question,
            "request_id": request_id,
            "conversation_id": conversation_id,
            "history": current_history,
        }

        final_context = ""

        async for namespace, mode, chunk in app.astream(
                graph_input,
                stream_mode=["updates", "messages"],
                subgraphs=True,
        ):
            branch_id = namespace[0] if namespace else "main"

            if mode == "updates":
                update_payload = normalize_update_payload(chunk)

                node_name = update_payload.get("node")
                node_values = update_payload.get("values")

                if not isinstance(node_values, dict):
                    continue

                # 컨텍스트가 넘어오면 변수에 저장해 둡니다 (히스토리용)
                if "context_text" in node_values:
                    final_context = node_values["context_text"]

                status_message = node_values.get("status_message")
                if status_message:
                    yield create_sse_event(
                        "status",
                        {
                            "type": "status",
                            "request_id": request_id,
                            "conversation_id": conversation_id,
                            "node": node_name,
                            "branch_id": branch_id,
                            "message": status_message,
                        },
                    )

                ui_status = node_values.get("ui_status")

                if ui_status:
                    yield create_sse_event(
                        "status",
                        {
                            "type": "status",
                            "request_id": request_id,
                            "conversation_id": conversation_id,
                            "node": node_name,
                            "code": ui_status.get("code"),
                            "message": ui_status.get("message"),
                            "detail": ui_status.get("detail"),
                        },
                    )

                context_docs = node_values.get("context_docs")
                if context_docs:
                    yield create_sse_event(
                        "context_docs",
                        {
                            "type": "context_docs",
                            "request_id": request_id,
                            "conversation_id": conversation_id,
                            "docs": context_docs,
                        },
                    )

                continue

            if mode == "messages":
                message_chunk, metadata = chunk

                if "hide_stream" in metadata.get("tags", []):
                    continue

                node_name = metadata.get("langgraph_node")

                chunk_text = extract_message_text(message_chunk)

                if not chunk_text:
                    continue

                match node_name:
                    case "status" | "classify_intent_status" | "groundedness_check":
                        yield create_sse_event(
                            "status_chunk",
                            {
                                "type": "status_chunk",
                                "request_id": request_id,
                                "conversation_id": conversation_id,
                                "node": node_name,
                                "branch_id": branch_id,
                                "message": chunk_text,
                            },
                        )
                        continue
                    # answer 노드에서 생성된 LLM 토큰은 본문 답변으로 전달
                    case "answer" | "direct_answer_from_history":
                        full_answer_parts.append(chunk_text)

                        yield create_sse_event(
                            "chunk",
                            {
                                "type": "chunk",
                                "request_id": request_id,
                                "conversation_id": conversation_id,
                                "node": node_name,
                                "message": chunk_text,
                            },
                        )
                        continue

        full_answer = "".join(full_answer_parts)
        
        # 2. 답변이 완료되면 히스토리에 누적
        if conversation_id:
            conversation_store[conversation_id].append({
                "question": question,
                "answer": full_answer,
                # "context": final_context
            })

        logger.info(
            (
                "SSE 답변 완료: "
                "request_id=%s, answer=%s"
            ),
            request_id,
            full_answer,
        )

        yield create_sse_event(
            "complete",
            {
                "type": "complete",
                "request_id": request_id,
                "conversation_id": conversation_id,
                "message": full_answer,
            },
        )

    except Exception:
        logger.exception(
            "SSE LangGraph 응답 처리 실패: request_id=%s",
            request_id,
        )

        yield create_sse_event(
            "error",
            {
                "type": "error",
                "request_id": request_id,
                "conversation_id": conversation_id,
                "code": "ANSWER_GENERATION_FAILED",
                "message": "답변 생성 중 오류가 발생했습니다.",
            },
        )

async def stream_agent_answer(
    request: ChatRequest,
) -> AsyncIterator[str]:
    request_id = request.request_id or str(uuid4())
    conversation_id = request.conversation_id
    question = request.message.strip()

    logger.info(
        (
            "SSE 질문 수신: "
            "request_id=%s, conversation_id=%s, question=%s"
        ),
        request_id,
        conversation_id,
        question,
    )

    yield create_sse_event(
        "start",
        {
            "type": "start",
            "request_id": request_id,
            "conversation_id": conversation_id,
        },
    )

    full_answer_parts: list[str] = []

    try:
        async for chunk in model_agent_service.stream_answer(
            question
        ):
            if chunk is None:
                continue



            chunk_text = str(chunk)

            if not chunk_text:
                continue

            full_answer_parts.append(chunk_text)

            yield create_sse_event(
                "chunk",
                {
                    "type": "chunk",
                    "request_id": request_id,
                    "conversation_id": conversation_id,
                    "message": chunk_text,
                },
            )

        full_answer = "".join(full_answer_parts)

        logger.info(
            (
                "SSE 답변 완료: "
                "request_id=%s, answer=%s"
            ),
            request_id,
            full_answer,
        )

        yield create_sse_event(
            "complete",
            {
                "type": "complete",
                "request_id": request_id,
                "conversation_id": conversation_id,
                "message": full_answer,
            },
        )

    except Exception:
        logger.exception(
            "SSE LLM 응답 처리 실패: request_id=%s",
            request_id,
        )

        yield create_sse_event(
            "error",
            {
                "type": "error",
                "request_id": request_id,
                "conversation_id": conversation_id,
                "code": "ANSWER_GENERATION_FAILED",
                "message": "답변 생성 중 오류가 발생했습니다.",
            },
        )




@router.post("")
async def chat_stream(
    request: ChatRequest,
) -> StreamingResponse:
    return StreamingResponse(
        stream_graph_answer(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
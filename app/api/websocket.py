from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.services.agent_service import agent_service
from app.services.stream_service import stream_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["websocket"],
)

async def send_json_if_connected(
    websocket: WebSocket,
    payload: dict[str, Any],
) -> None:
    if websocket.application_state != WebSocketState.CONNECTED:
        return

    await websocket.send_json(payload)

@router.websocket("/ws/chat")
async def chat_websocket(
    websocket: WebSocket,
) -> None:
    await websocket.accept()

    logger.info(
        "웹 WebSocket 연결됨: client=%s",
        websocket.client,
    )

    try:
        while True:
            request = await websocket.receive_json()

            request_id = str(
                request.get("request_id") or uuid4()
            )
            conversation_id = request.get("conversation_id")
            question = str(
                request.get("message", "")
            ).strip()

            if not question:
                await websocket.send_json(
                    {
                        "type": "error",
                        "request_id": request_id,
                        "conversation_id": conversation_id,
                        "code": "EMPTY_QUESTION",
                        "message": "질문을 입력해 주세요.",
                    }
                )
                continue

            logger.info(
                "웹 질문 수신: request_id=%s, conversation_id=%s, question=%s",
                request_id,
                conversation_id,
                question,
            )

            await websocket.send_json(
                {
                    "type": "start",
                    "request_id": request_id,
                    "conversation_id": conversation_id,
                }
            )

            async def send_chunk(chunk: str) -> None:
                await websocket.send_json(
                    {
                        "type": "chunk",
                        "request_id": request_id,
                        "conversation_id": conversation_id,
                        "message": chunk,
                    }
                )

            try:
                full_answer = await stream_service.forward(
                    source=agent_service.stream_answer(question),
                    sender=send_chunk,
                )

                await websocket.send_json(
                    {
                        "type": "complete",
                        "request_id": request_id,
                        "conversation_id": conversation_id,
                        "message": full_answer,
                    }
                )

            except WebSocketDisconnect:
                raise

            except Exception:
                logger.exception(
                    "웹 LLM 응답 처리 실패: request_id=%s",
                    request_id,
                )

                await send_json_if_connected(
                    websocket,
                    {
                        "type": "error",
                        "request_id": request_id,
                        "conversation_id": conversation_id,
                        "code": "ANSWER_GENERATION_FAILED",
                        "message": "답변 생성 중 오류가 발생했습니다.",
                    },
                )

    except WebSocketDisconnect:
        logger.info(
            "웹 WebSocket 연결 종료: client=%s",
            websocket.client,
        )

    except ValueError as error:
        logger.warning(
            "잘못된 WebSocket 요청: %s",
            error,
        )

        await send_json_if_connected(
            websocket,
            {
                "type": "error",
                "code": "INVALID_REQUEST",
                "message": str(error),
            },
        )

    except Exception:
        logger.exception(
            "WebSocket 처리 중 예상하지 못한 오류가 발생했습니다."
        )

        await send_json_if_connected(
            websocket,
            {
                "type": "error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": "서버 처리 중 오류가 발생했습니다.",
            },
        )
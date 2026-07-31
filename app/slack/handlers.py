from __future__ import annotations

import logging
import re
from idlelib.debugger_r import start_remote_debugger
from typing import Any

from slack_bolt.async_app import AsyncApp

from app.services.agent_service import agent_service
from app.services.model_agent_service import model_agent_service
from app.services.stream_service import stream_service

logger = logging.getLogger(__name__)

def remove_bot_mention(text: str) -> str:
    """
    Slack 메시지에 포함된 <@U12345678> 형태의 멘션을 제거합니다.
    :param text:
    :return:
    """
    return re.sub(r"<@[A-Z0-9]+>", "", text).strip()

async def process_slack_question(
        *,
        event: dict[str, Any],
        say_stream: Any,
        remove_metion: bool,
) -> None:
    if event.get("bot_id"):
        return

    if event.get("subtype"):
        return

    question = str(event.get("text", "")).strip()

    if remove_metion:
        question = remove_bot_mention(question)

    logger.info(
        "Slack 질문 수신: type:%s, user=%s, channel=%s, quseion=%s",
        event.get("type"),
        event.get("user"),
        event.get("channel"),
        question,
    )

    stream = None

    try:
        stream = await say_stream()

        if not question:
            await stream.append(
                markdown_text="질문을 입력해 주세요.",
            )
            await stream.stop()

        # async def send_chunk(chunk: str) -> None:
        #     await stream.append(
        #         markdown_text=chunk,
        #     )

        # await stream_service.forward(
        #     source=agent_service.stream_answer(question),
        #     sender=send_chunk,
        # )

        async for chunk in model_agent_service.stream_answer(question):
            await stream.append(
                markdown_text=chunk,
            )
        await stream.stop()

    except Exception as e:
        logger.exception("Slack LLM 응답 처리 중 오류가 발생 했습니다.")

        if stream is not None:
            try:
                await stream.append(
                    markdown_text="\n\n답변 생성 중 오류가 발생 했습니다.",
                )
                await stream.stop()
            except Exception as e:
                logger.exception("Slack 오류 메시지 전송에 실패 했습니다.")

def register_slack_handlers(slack_app: AsyncApp) -> None:
    @slack_app.event("app_mention")
    async def handle_app_mention(
            event: dict[str, Any],
            say_stream: Any,
    ) -> None:
        await process_slack_question(
            event=event,
            say_stream=say_stream,
            remove_metion=True,
        )

    @slack_app.event("message")
    async def handle_direct_message(
            event: dict[str, Any],
            say_stream: Any,
    ) -> None:
        # mession.im 만 처리 합니다.
        # 채널의 일반 message 이벤트는 무시합니다.
        if event.get("channel_type") != "im":
            return

        await process_slack_question(
            event=event,
            say_stream=say_stream,
            remove_metion=False,
        )

    @slack_app.error
    async def handle_slack_error(
            error: Exception,
            body: dict[str, Any],
            logger: logging.Logger,
    ) -> None:
        logger.exception(
            "Slack 이벤트 처리 오류: %s",
            error
        )
        logger.error(
            "Slack 이벤트 본문: %s",
            body,
        )


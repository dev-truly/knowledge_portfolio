from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Any

from slack_bolt.adapter.socket_mode.async_handler import (
    AsyncSocketModeHandler,
)
from slack_bolt.async_app import AsyncApp

from app.core.config import settings
from app.slack.handlers import register_slack_handlers

logger = logging.getLogger(__name__)

class SlackSocketModeService:
    def __init__(self) -> None:
        self._slack_app = AsyncApp(
            token=settings.slack_bot_token,
        )

        register_slack_handlers(self._slack_app)

        self._handler: AsyncSocketModeHandler | None = None
        self._task: asyncio.Task[Any] | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.is_running:
            logger.warning("Slack Socket Mode가 이미 실행중 입니다.")
            return

        logger.info("Slack Socket Mode를 시작 합니다.")

        # 반드시 실행 중인 이벤트 루프 안에서 생성합니다.
        self._handler = AsyncSocketModeHandler(
            self._slack_app,
            app_token=settings.slack_app_token,
        )

        self._task = asyncio.create_task(
            self._handler.start_async(),
            name="slack-socket-mode",
        )

        self._task.add_done_callback(
            self._handler_task_done,
        )

        await self._log_auth_information()

    async def stop(self) -> None:
        logger.info("Slack Socket Mode를 종료합니다.")

        if self._handler is not None:
            try:
                await self._handler.close_async()

            except Exception as e:
                logger.exception("Slack Socket Mode 연결 종료 중 오류가 발생했습니다.")

            if self._task is not None:
                self._task.cancel()

                with suppress(asyncio.CancelledError):
                    await self._task

            self._task = None
            self._handler = None

    async def _log_auth_information(self) -> None:
        try:
            auth_result = await self._slack_app.client.auth_test()

            logger.info(
                "Slack 인증 완료: team=%s, bot=%s, user_id=%s",
                auth_result.get("team"),
                auth_result.get("user"),
                auth_result.get("user_id"),
            )
        except Exception as e:
            logger.exception("Slack Bot Token 인증 확인에 실패 했습니다.")
            raise

    @staticmethod
    def _handler_task_done(task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            return

        exception = task.exception()

        if exception is not None:
            logger.exception(
                "Slack Socket Mode 태스크가 비정상 종료 되었습니다.",
                exc_info=exception,
            )

slack_socket_mode_service = SlackSocketModeService()

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api import health, websocket, sse_stream, questions
from app.core.config import settings
from app.mcp.client import mcp_client_service
from app.services.agent_service import agent_service
from app.slack.socket_mode import slack_socket_mode_service
from fastapi.middleware.cors import CORSMiddleware


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(
            logging,
            settings.log_level.upper(),
            logging.INFO,
        ),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    logger.info(
        "애플리케이션 시작: name=%s, env=%s",
        settings.app_name,
        settings.app_env,
    )

    try:
        # 1. MCP 서버 연결 및 Tool 로딩
        await mcp_client_service.initialize()

        # 2. MCP Tool을 주입한 Agent 생성
        await agent_service.initialize()

        # 3. Slack Socket Mode 시작
        await slack_socket_mode_service.start()

        yield

    finally:
        # 시작 중간에 실패하더라도 종료 로직 수행
        try:
            await slack_socket_mode_service.stop()
        except Exception:
            logger.exception(
                "Slack Socket Mode 종료 실패"
            )

        try:
            await agent_service.close()
        except Exception:
            logger.exception(
                "AgentService 종료 실패"
            )

        try:
            await mcp_client_service.close()
        except Exception:
            logger.exception(
                "MCP Client 종료 실패"
            )

        logger.info(
            "애플리케이션 종료: name=%s",
            settings.app_name,
        )


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(websocket.router)
app.include_router(sse_stream.router)
app.include_router(questions.router)


for route in app.routes:
    logger.info(
        "등록 라우트: type=%s, path=%s, name=%s",
        route.__class__.__name__,
        getattr(route, "path", None),
        getattr(route, "name", None),
    )
@app.get("/")
async def root() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "status": "running",
    }
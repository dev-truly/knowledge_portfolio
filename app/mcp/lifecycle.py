from __future__ import annotations

import logging

from app.mcp.client import mcp_client_service

logger = logging.getLogger(__name__)


async def start_mcp() -> None:
    logger.info("MCP 서비스를 시작합니다.")
    await mcp_client_service.initialize()


async def stop_mcp() -> None:
    logger.info("MCP 서비스를 종료합니다.")
    await mcp_client_service.close()
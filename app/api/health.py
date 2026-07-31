from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.mcp.client import mcp_client_service
from app.services.agent_service import agent_service

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "agent_initialized": (
            agent_service.is_initialized
        ),
        "mcp_initialized": (
            mcp_client_service.is_initialized
        ),
        "mcp_tools": (
            mcp_client_service.tool_names
        ),
    }


@router.get("/mcp")
async def mcp_health() -> dict[str, Any]:
    return await mcp_client_service.health_check()
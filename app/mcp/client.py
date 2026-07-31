from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.mcp.config import build_mcp_server_config

logger = logging.getLogger(__name__)


class MCPClientService:
    def __init__(self) -> None:
        self._client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] = []
        self._lock = asyncio.Lock()

    @property
    def tools(self) -> list[BaseTool]:
        """
        외부에서 내부 Tool 목록을 직접 수정하지 못하도록
        복사본을 반환합니다.
        """
        return list(self._tools)

    @property
    def tool_names(self) -> list[str]:
        return [tool.name for tool in self._tools]

    @property
    def is_initialized(self) -> bool:
        """
        MCP Client와 Tool 목록이 모두 준비된 경우에만
        초기화 완료로 판단합니다.
        """
        return (
            self._client is not None
            and len(self._tools) > 0
        )

    async def initialize(self) -> None:
        """
        MCP 서버에 연결해 Tool 목록을 불러옵니다.

        여러 coroutine이 동시에 initialize()를 호출해도
        한 번만 초기화되도록 Lock으로 보호합니다.
        """
        if self.is_initialized:
            return

        async with self._lock:
            if self.is_initialized:
                return

            await self._initialize_unlocked()

    async def _initialize_unlocked(self) -> None:
        """
        반드시 self._lock을 획득한 상태에서 호출해야 합니다.

        initialize()와 reload_tools()가 같은 초기화 코드를
        안전하게 재사용하기 위한 내부 메서드입니다.
        """
        config = build_mcp_server_config()

        if not config:
            raise RuntimeError(
                "MCP 서버 설정이 존재하지 않습니다."
            )

        logger.info(
            "MCP Client 초기화 시작: servers=%s",
            list(config.keys()),
        )

        client = MultiServerMCPClient(config)

        try:
            tools = await client.get_tools()

            if not tools:
                raise RuntimeError(
                    "MCP 서버에서 Tool을 불러오지 못했습니다."
                )

            self._client = client
            self._tools = list(tools)

            logger.info(
                "MCP Tool 로딩 완료: count=%d, tools=%s",
                len(self._tools),
                self.tool_names,
            )

        except Exception:
            logger.exception(
                "MCP Client 초기화에 실패했습니다."
            )

            self._client = None
            self._tools = []

            raise

    async def reload_tools(self) -> None:
        """
        MCP Tool 목록을 다시 불러옵니다.

        Tool을 추가하거나 MCP 서버 구현이 변경된 후
        Tool 정의를 다시 로딩할 때 사용합니다.

        주의:
        이미 생성된 LangChain Agent에는 이전 Tool 목록이
        주입되어 있으므로, reload_tools() 이후 Agent도
        다시 생성해야 합니다.
        """
        async with self._lock:
            logger.info("MCP Tool을 다시 로딩합니다.")

            # 기존 상태를 먼저 제거하고 새 Client를 생성합니다.
            self._client = None
            self._tools = []

            await self._initialize_unlocked()

        def get_tool(
                self,
                tool_name: str,
        ) -> BaseTool | None:
            """
            이름으로 MCP Tool을 조회합니다.
            """
            return next(
                (
                    tool
                    for tool in self._tools
                    if tool.name == tool_name
                ),
                None,
            )

        def require_tool(
                self,
                tool_name: str,
        ) -> BaseTool:
            """
            이름으로 MCP Tool을 조회합니다.

            Tool이 없으면 예외를 발생시킵니다.
            """
            tool = self.get_tool(tool_name)

            if tool is None:
                raise RuntimeError(
                    f"MCP Tool을 찾을 수 없습니다: {tool_name}"
                )

            return tool

        async def invoke_tool(
                self,
                tool_name: str,
                arguments: dict[str, Any] | None = None,
        ) -> Any:
            """
            Agent를 거치지 않고 특정 MCP Tool을 직접 호출합니다.

            Health Check나 관리자 API처럼 특정 Tool을
            명시적으로 실행해야 할 때 사용할 수 있습니다.
            """
            if not self.is_initialized:
                await self.initialize()

            tool = self.require_tool(tool_name)

            return await tool.ainvoke(arguments or {})

        async def health_check(self) -> dict[str, Any]:
            """
            MCP의 agent_health Tool을 호출해
            실제 Agent API 연결 상태까지 점검합니다.
            """
            if not self.is_initialized:
                return {
                    "status": "not_initialized",
                    "tools": [],
                }

            if self.get_tool("agent_health") is None:
                return {
                    "status": "tool_not_found",
                    "message": (
                        "agent_health Tool이 등록되어 있지 않습니다."
                    ),
                    "tools": self.tool_names,
                }

            try:
                result = await self.invoke_tool(
                    tool_name="agent_health",
                )

                return {
                    "status": "ok",
                    "result": result,
                    "tools": self.tool_names,
                }

            except Exception as exc:
                logger.exception(
                    "MCP agent_health 호출에 실패했습니다."
                )

                return {
                    "status": "error",
                    "error": str(exc),
                    "tools": self.tool_names,
                }

        async def close(self) -> None:
            """
            MCP ClientService의 내부 상태를 정리합니다.

            MultiServerMCPClient의 기본 stateless Tool 호출에서는
            각 Tool 실행 단위로 MCP 세션이 정리됩니다.
            """
            logger.info("MCP Client를 종료합니다.")

            async with self._lock:
                self._tools = []
                self._client = None

mcp_client_service = MCPClientService()
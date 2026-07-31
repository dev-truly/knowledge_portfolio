# app/mcp/config.py

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_mcp_server_config() -> dict[str, dict[str, Any]]:
    return {
        "agent-search": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                "-m",
                "mcp_servers.agent_search.server",
            ],
            "cwd": str(PROJECT_ROOT),
            "env": {
                **os.environ,
                "PYTHONPATH": str(PROJECT_ROOT),
                "MCP_TRANSPORT": "stdio",
            },
        }
    }
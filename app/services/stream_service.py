from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable

logger = logging.getLogger(__name__)

ChunkSender = Callable[[str], Awaitable[None]]

class StreamService:
    def __init__(
        self,
        *,
        flush_interval_seconds: float= 0.05,
        minimum_buffer_size: int= 1,
    ) -> None:
        self._flush_interval_seconds = flush_interval_seconds
        self._minimum_buffer_size = minimum_buffer_size

    async def forward(
            self,
            source: AsyncIterator[str],
            sender: ChunkSender,
    ) -> str:
        """
        source에서 받은 청크를 sender로 전달 합니다.

        반환값:
            전체 누적 답변
        :param source:
        :param sender:
        :return:
        """
        full_answer = ""
        buffer = ""

        async for chunk in source:
            if not chunk:
                continue

            full_answer += chunk
            buffer += chunk

            if len(buffer) >= self._minimum_buffer_size:
                continue

            await sender(buffer)
            buffer = ""

            if self._flush_interval_seconds > 0:
                await asyncio.sleep(self._flush_interval_seconds)

        if buffer:
            await sender(buffer)

            return full_answer

stream_service = StreamService(
    flush_interval_seconds=0.02,
    minimum_buffer_size=1,
)
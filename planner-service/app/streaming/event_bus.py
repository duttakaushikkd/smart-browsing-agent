import asyncio
from collections import defaultdict

from app.schemas.events import StreamEvent


class EventBus:
    """In-process pub/sub used by WebSocket streams.

    For multi-replica production deployments, replace this adapter with Redis
    pub/sub or a broker while preserving the publish/subscribe contract.
    """

    def __init__(self) -> None:
        self._queues: dict[str, set[asyncio.Queue[StreamEvent]]] = defaultdict(set)

    async def publish(self, event: StreamEvent) -> None:
        for queue in list(self._queues[event.session_id]):
            await queue.put(event)

    async def subscribe(self, session_id: str) -> asyncio.Queue[StreamEvent]:
        queue: asyncio.Queue[StreamEvent] = asyncio.Queue(maxsize=100)
        self._queues[session_id].add(queue)
        return queue

    async def unsubscribe(self, session_id: str, queue: asyncio.Queue[StreamEvent]) -> None:
        self._queues[session_id].discard(queue)
        if not self._queues[session_id]:
            del self._queues[session_id]

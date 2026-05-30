from __future__ import annotations
import asyncio
import time
from typing import Any
import structlog
from playwright.async_api import BrowserContext, Page
from browser.pool import BrowserPool

logger = structlog.get_logger(__name__)


class ActiveSession:
    def __init__(self, session_id: str, context: BrowserContext) -> None:
        self.session_id = session_id
        self.context = context
        self.last_active = time.perf_counter()
        self.default_page = None

    async def get_active_page(self) -> Page:
        self.last_active = time.perf_counter()
        pages = self.context.pages
        if not pages:
            page = await self.context.new_page()
            return page
        return pages[0]

    def update_activity(self) -> None:
        self.last_active = time.perf_counter()


class BrowserSessionManager:
    """Orchestrates browser contexts, tab states, and idle session collection."""

    def __init__(self, pool: BrowserPool, idle_timeout: float = 300.0) -> None:
        self._pool = pool
        self._idle_timeout = idle_timeout
        self._sessions: dict[str, ActiveSession] = {}
        self._cleanup_task = None

    async def start(self) -> None:
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("session_manager_cleanup_loop_started")

    async def create_session(self, session_id: str) -> ActiveSession:
        if session_id in self._sessions:
            logger.info("reusing_existing_session", session_id=session_id)
            session = self._sessions[session_id]
            session.update_activity()
            return session

        context = await self._pool.create_context()
        session = ActiveSession(session_id, context)
        self._sessions[session_id] = session
        logger.info("session_created", session_id=session_id)
        return session

    async def get_session(self, session_id: str) -> ActiveSession:
        session = self._sessions.get(session_id)
        if not session:
            logger.info("session_not_found_creating_on_the_fly", session_id=session_id)
            session = await self.create_session(session_id)
        session.update_activity()
        return session

    async def close_session(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if session:
            logger.info("closing_session", session_id=session_id)
            await session.context.close()
            return True
        return False

    async def stop(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
        for session_id in list(self._sessions.keys()):
            await self.close_session(session_id)

    async def _cleanup_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(30)
                now = time.perf_counter()
                for session_id, session in list(self._sessions.items()):
                    if now - session.last_active > self._idle_timeout:
                        logger.info("cleaning_up_idle_session", session_id=session_id)
                        await self.close_session(session_id)
        except asyncio.CancelledError:
            pass

from abc import ABC, abstractmethod
from copy import deepcopy

from redis.asyncio import Redis

from app.schemas.state import AgentSession


class SessionNotFoundError(KeyError):
    """Raised when a session does not exist in memory."""


class SessionStore(ABC):
    @abstractmethod
    async def create(self, session: AgentSession) -> AgentSession:
        """Persist a new session."""

    @abstractmethod
    async def get(self, session_id: str) -> AgentSession:
        """Return a session by id."""

    @abstractmethod
    async def save(self, session: AgentSession) -> None:
        """Persist changes to an existing session."""


class InMemorySessionStore(SessionStore):
    """Process-local store for tests and local development."""

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    async def create(self, session: AgentSession) -> AgentSession:
        self._sessions[session.session_id] = deepcopy(session)
        return deepcopy(session)

    async def get(self, session_id: str) -> AgentSession:
        try:
            return deepcopy(self._sessions[session_id])
        except KeyError as exc:
            raise SessionNotFoundError(session_id) from exc

    async def save(self, session: AgentSession) -> None:
        self._sessions[session.session_id] = deepcopy(session)


class RedisSessionStore(SessionStore):
    """Redis-backed session store for stateless API replicas."""

    def __init__(self, redis: Redis, ttl_seconds: int = 86_400) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    def _key(self, session_id: str) -> str:
        return f"agent-session:{session_id}"

    async def create(self, session: AgentSession) -> AgentSession:
        await self.save(session)
        return session

    async def get(self, session_id: str) -> AgentSession:
        raw = await self._redis.get(self._key(session_id))
        if raw is None:
            raise SessionNotFoundError(session_id)
        return AgentSession.model_validate_json(raw)

    async def save(self, session: AgentSession) -> None:
        await self._redis.set(
            self._key(session.session_id),
            session.model_dump_json(),
            ex=self._ttl_seconds,
        )

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.api.health import router as health_router
from app.api.routes import router as agent_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.security import UrlPolicy
from app.memory.store import InMemorySessionStore, RedisSessionStore, SessionStore
from app.memory.summarizer import MemorySummarizer
from app.planner.engine import PlannerEngine
from app.planner.llm import create_planner_model
from app.planner.tools import ToolRegistry, create_browser_api_tools
from app.recovery.engine import RecoveryEngine
from app.services.browser_client import BrowserServiceClient
from app.streaming.event_bus import EventBus

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    app.state.settings = settings
    app.state.redis = None

    if settings.use_redis:
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        app.state.redis = redis
        store: SessionStore = RedisSessionStore(redis)
    else:
        store = InMemorySessionStore()

    browser_client = BrowserServiceClient(
        base_url=settings.browser_service_url,
        timeout_seconds=settings.browser_timeout_seconds,
    )
    event_bus = EventBus()
    tools = ToolRegistry(create_browser_api_tools(browser_client, UrlPolicy(settings)))
    app.state.session_store = store
    app.state.event_bus = event_bus
    app.state.planner_engine = PlannerEngine(
        settings=settings,
        store=store,
        model=create_planner_model(settings),
        tool_registry=tools,
        events=event_bus,
        summarizer=MemorySummarizer(),
        recovery=RecoveryEngine(),
    )
    logger.info("planner_service_started", environment=settings.environment)
    yield
    if app.state.redis:
        await app.state.redis.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.include_router(health_router)
    app.include_router(agent_router)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        del request
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    return app


app = create_app()

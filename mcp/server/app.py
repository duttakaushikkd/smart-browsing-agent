from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from browser_client.client import BrowserServiceClient
from config.settings import Settings, get_settings
from executors.engine import ToolExecutorEngine
from observability.logging import configure_logging
from observability.middleware import CorrelationIdMiddleware
from registry.registry import ToolRegistry
from security.url_policy import UrlPolicy
from server.runtime import McpToolService
from tools.factory import create_browser_tools
from transport.http import create_http_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    browser_client = BrowserServiceClient(
        base_url=settings.browser_service_url,
        timeout_seconds=settings.browser_timeout_seconds,
    )
    registry = ToolRegistry(create_browser_tools(browser_client, UrlPolicy(settings)))
    executor = ToolExecutorEngine(
        registry=registry,
        timeout_seconds=settings.tool_timeout_seconds,
        max_retries=settings.max_tool_retries,
    )
    app.state.browser_client = browser_client
    app.state.tool_service = McpToolService(registry=registry, executor=executor)
    logger.info("mcp_server_started", environment=settings.environment, tools=len(registry.names()))
    yield
    await browser_client.aclose()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved)
    app = FastAPI(title=resolved.app_name, version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(create_http_router(lambda request: request.app.state.tool_service))
    return app


app = create_app()

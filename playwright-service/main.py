import uvicorn
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import structlog
from config.settings import get_settings
from observability.logging import configure_logging
from observability.middleware import CorrelationIdMiddleware
from security.url_policy import UrlPolicy
from browser.pool import BrowserPool
from sessions.manager import BrowserSessionManager
from api.routes import router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)

    pool = BrowserPool()
    await pool.initialize()

    manager = BrowserSessionManager(pool, idle_timeout=settings.session_idle_timeout_seconds)
    await manager.start()

    app.state.browser_pool = pool
    app.state.session_manager = manager
    app.state.url_policy = UrlPolicy(settings)

    logger.info("playwright_service_started", port=settings.port)
    yield
    await manager.stop()
    await pool.close()
    logger.info("playwright_service_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "local",
        reload_excludes=[".venv/*", "**/__pycache__/*"],
    )


if __name__ == "__main__":
    main()

import uvicorn

from config.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "server.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "local",
        reload_excludes=[".venv/*", "**/__pycache__/*"],
    )


if __name__ == "__main__":
    main()

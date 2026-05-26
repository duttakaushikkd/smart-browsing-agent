FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY config ./config
COPY observability ./observability
COPY security ./security
COPY schemas ./schemas
COPY registry ./registry
COPY browser_client ./browser_client
COPY tools ./tools
COPY executors ./executors
COPY transport ./transport
COPY server ./server
COPY main.py ./

RUN uv pip install --system ".[dev]"

EXPOSE 9000

CMD ["python", "main.py"]

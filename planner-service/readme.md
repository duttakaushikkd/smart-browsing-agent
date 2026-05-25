# Smart Browsing Agent Planner

Production-grade FastAPI planner service for a Smart Browsing Agent architecture:

```text
Frontend -> Planner Agent Service -> External Browser Service APIs -> Playwright Workers
```

The planner owns goal interpretation, state, tool calling, replanning, progress streaming, and recovery. It does not import Playwright, manipulate the DOM, or execute browser actions directly.

## Architecture

```text
app/
  api/        FastAPI HTTP and WebSocket routes
  planner/    LLM interface, tool registry, and orchestration loop
  memory/     session persistence and summarization
  prompts/    reusable planner, replanning, recovery, extraction, summarization prompts
  schemas/    request/response/tool/event/state schemas
  services/   external API clients and circuit breaker
  streaming/  WebSocket event bus abstraction
  observability/ tracing, latency, execution timeline support
  recovery/   autonomous recovery policy engine
  core/       configuration, logging, URL policy
  utils/      small shared utilities
  tests/      unit and integration tests
```

## API

Start a session:

```bash
curl -X POST http://localhost:8000/agent/start \
  -H 'content-type: application/json' \
  -d '{"goal":"Open https://example.com and extract the main page text"}'
```

Response:

```json
{
  "session_id": "abc",
  "state": "planning"
}
```

Continue after clarification:

```bash
curl -X POST http://localhost:8000/agent/abc/continue \
  -H 'content-type: application/json' \
  -d '{"user_input":"Use https://example.com"}'
```

Get status:

```bash
curl http://localhost:8000/agent/abc/status
```

Cancel:

```bash
curl -X POST http://localhost:8000/agent/abc/cancel
```

Stream progress:

```text
ws://localhost:8000/agent/{session_id}/stream
```

Events include `state`, `plan`, `action`, `tool_result`, `observation`, `error`, and `completion`. Hidden reasoning is never streamed.

## Browser Tool Contract

The planner calls the external browser executor through:

```http
POST /browser/action
```

Request:

```json
{
  "session_id": "abc",
  "action": "click_element",
  "payload": {
    "target_ref": "element:login-button"
  }
}
```

Expected response:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {}
}
```

Implemented tools:

- `open_url`
- `click_element`
- `type_text`
- `extract_text`
- `screenshot`
- `wait_for_element`
- `get_dom_snapshot`
- `scroll_page`
- `go_back`

All tools validate arguments with Pydantic before calling the browser service. `get_dom_snapshot` is expected to return compressed semantic observations such as visible buttons, links, inputs, and actionable regions, not full raw HTML.

## LLM Planning

The service uses OpenAI SDK-compatible chat completions with tool calling. Set:

```bash
OPENAI_API_KEY=...
OPENAI_BASE_URL=... # optional compatible endpoint
OPENAI_MODEL=gpt-4.1-mini
BROWSER_SERVICE_URL=http://browser-service:8080
```

If no API key is configured, a deterministic local heuristic planner is used for tests and local smoke checks.

## Reliability And Security

- Async-first execution with explicit `AgentState`
- Retry and timeout handling for browser service calls
- Circuit breaker around the browser service
- Anti-loop protection for repeated failed tool calls
- Autonomous recovery for stale targets, missing elements, timeouts, empty observations, and unexpected navigation
- Max step and per-step timeout limits
- URL allow/block list and SSRF-oriented host blocking
- Session isolation by `session_id`
- Rate limiting through `slowapi`
- Structured JSON logs with `structlog`
- Token usage and execution timeline in session status

## Run Locally

```bash
uv venv
uv pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

Docker:

```bash
cp .env.example .env
docker compose up --build
```

## Notes For Production

- Use `USE_REDIS=true` so API replicas remain stateless.
- Point `BROWSER_SERVICE_URL` at the separately deployed browser executor API.
- Use Redis pub/sub or a broker for WebSocket events when scaling beyond one planner process.
- Enforce human approval checkpoints in the frontend or planner policy for login, payment, booking, and private data workflows.

# Implementation reference — read before coding

Use this doc as **orientation and guardrails** before changing behavior, APIs, or cross-service contracts. Prefer **minimal diffs**, match **existing layout and patterns**, and keep **source of truth** in code alongside this summary.

Canonical backend documentation: `planner-service/readme.md`

---

## 1. Repository map

| Path | Role |
|------|------|
| `planner-service/` | **Product backend**: FastAPI planner (sessions, LLM tool loop, streaming, Redis/in-memory persistence). Entry: `app/main.py`. |
| `frontend-ui/` | **Product UI**: Next.js 15 (App Router), Zustand, planner HTTP + WebSocket client. Entry: `src/app/`. |
| `mcp/` | **Standalone MCP tool server**: registry, execution, browser client, HTTP transport. Entry: `mcp/main.py`. |
| `playwright-service/` | **Stub** (readme only). Real browser executor is **outside** this repo; MCP server talks to it via HTTP. |
| `main.py` (repo root) | IDE stub (**not** the application). |
| Root `package-lock.json` | Empty workspace lock; **use** `frontend-ui/package-lock.json` for the app. |

---

## 2. System architecture (high level)

```text
Frontend (Next.js)  --HTTP/WS-->  Planner (FastAPI)  --HTTP-->  MCP Tool Server  --HTTP-->  Browser executor API  -->  Playwright workers (external)
```

- The **planner** owns goals, agent state, recovery, timelines, and WebSocket updates. It invokes tools **only** via `app/services/mcp_client/` (no local tool registry).
- The **MCP server** owns tool registry, schemas, execution, URL policy, and browser service communication.
- The **frontend** starts sessions, opens a WebSocket stream, and surfaces status / messages.
- **Scaling**: session store can use Redis (`USE_REDIS`); in-process `EventBus` does not span multiple planner processes without extra work (see `planner-service/readme.md` production notes).

---

## 3. Stack and tooling

**Planner** (`planner-service/pyproject.toml`)

- Python **≥ 3.12**, FastAPI, Uvicorn, Pydantic v2 + pydantic-settings, httpx, OpenAI SDK, Redis (optional), structlog, slowapi (rate limit).
- Quality: Ruff (line length **100**), mypy strict + pydantic plugin, pytest + pytest-asyncio (`app/tests`).

**Frontend** (`frontend-ui/package.json`)

- TypeScript (strict), Next.js **15**, React 18, Tailwind, Zustand.
- `npm run lint` — ESLint 9; `npm run test` — Vitest.

**CI**

- No `.github/` workflows in-repo; treat **pytest**, **ruff/mypy** (planner), and **lint/test** (frontend) as the expected local gates before merge.

---

## 4. Where to change what

### Planner (`planner-service/app/`)

| Area | Typical files |
|------|----------------|
| HTTP + WebSocket routes | `api/routes.py`, `api/health.py`, `api/dependencies.py` |
| Agent loop, LLM | `planner/engine.py`, `planner/llm.py` |
| Remote MCP tools | `services/mcp_client/` |
| Schemas (API, events, session) | `schemas/` |
| Session persistence | `memory/store.py`, `memory/summarizer.py` |
| Streaming to clients | `streaming/event_bus.py` |
| Recovery policy | `recovery/engine.py` |
| Config / logging | `core/config.py`, `core/logging.py` |
| Prompt text | `prompts/*.md` |

### Frontend (`frontend-ui/src/`)

| Area | Typical files |
|------|----------------|
| Pages / layout | `app/page.tsx`, `app/layout.tsx` |
| Global state + WebSocket wiring | `store/useAppStore.ts` |
| Planner API / stream | `services/plannerApi.ts`, `services/plannerSocket.ts`, `services/plannerEvents.ts`, `services/plannerSessionStorage.ts` |
| Shared types | `types/index.ts` |
| UI | `components/*`, `hooks/*`, `lib/utils.ts` |

**Import alias**: `@/*` → `src/*` (`frontend-ui/tsconfig.json`).

### MCP tool server (`mcp/`)

| Area | Typical files |
|------|----------------|
| HTTP app + lifespan | `server/app.py`, `main.py` |
| Transport (HTTP) | `transport/http.py` |
| Tool registry / executor | `registry/`, `executors/` |
| Browser tools | `tools/browser_actions.py`, `tools/factory.py` |
| Browser HTTP client | `browser_client/client.py` |
| Security / URL policy | `security/` |
| Schemas | `schemas/` |

---

## 5. Contracts (do not drift casually)

### 5.1 Planner HTTP (FastAPI prefix `/agent`)

Implemented in `planner-service/app/api/routes.py`:

| Method | Path | Notes |
|--------|------|--------|
| POST | `/agent/start` | **202**; body `StartAgentRequest` (`goal`, optional `metadata`) → `session_id`, `state`. |
| POST | `/agent/{session_id}/continue` | Optional `user_input`; returns full `AgentStatusResponse`. |
| GET | `/agent/{session_id}/status` | `AgentStatusResponse` (timeline, `metadata` merges `token_usage` in handler). |
| POST | `/agent/{session_id}/cancel` | Cancels planner task for session. |

Pydantic models: `planner-service/app/schemas/agent.py`, session shape in `schemas/state.py`.

Frontend client (**source of truth for UI URLs**): `frontend-ui/src/services/plannerApi.ts`  
Environment: `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).

### 5.2 WebSocket

- URL: `/agent/{session_id}/stream` (see `getStreamUrl` in `plannerApi.ts`).
- First server message is a synthetic **connected** payload; idle **heartbeat** JSON every ~30s (`routes.py`).
- Streaming payload shape: `planner-service/app/schemas/events.py` (`StreamEvent`, etc.). Frontend parsing/normalization: `plannerEvents.ts` (handles mixed casing for `state`).

### 5.3 Browser executor (external service)

Planner posts to **`POST {BROWSER_SERVICE_URL}/browser/action`** with JSON:

```json
{ "session_id": "...", "action": "<tool_name>", "payload": { } }
```

Response shape: `{ "success", "data", "error", "metadata" }` (see `planner-service/app/schemas/tools.py`).

Tool names and semantics: listed in `planner-service/readme.md` — `open_url`, `click_element`, `type_text`, `extract_text`, `screenshot`, `wait_for_element`, `get_dom_snapshot`, `scroll_page`, `go_back`.

`open_url` is subject to **allow/block lists** (`Settings.allowed_domains` / `blocked_domains` in `core/config.py`; enforcement in `core/security.py`).

---

## 6. Configuration (planner)

Loaded via **pydantic-settings** from env (and `.env` in `planner-service`): `app/core/config.py`.  
Template: `planner-service/.env.example`.

Important keys:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` | LLM; **no key** ⇒ heuristic planner (`planner/llm.py`) for local/test. |
| `BROWSER_SERVICE_URL`, `BROWSER_TIMEOUT_SECONDS` | External browser API. |
| `USE_REDIS`, `REDIS_URL` | Session backend. |
| `CORS_ORIGINS` | CSV → list (lowercased domains in allow/block parsers). |
| `ALLOWED_DOMAINS`, `BLOCKED_DOMAINS` | URL policy for navigations. |
| `MAX_AGENT_STEPS`, `MAX_TOOL_RETRIES`, `AGENT_STEP_TIMEOUT_SECONDS` | Loop limits / timeouts. |
| `RATE_LIMIT` | slowapi (e.g. `60/minute`). |

Docker: `planner-service/docker-compose.yml` (Redis + planner; browser often on host — see compose `BROWSER_SERVICE_URL`).

---

## 7. Implementation checklist (before opening a PR)

1. **Scope**: Touch only the planner **or** frontend **or** both** if the contract demands it — avoid drive-by edits in stubs (`playwright-service/`, `mcp/`, root `main.py`).
2. **Contracts**: If you change request/response or WebSocket fields, update **`schemas/`**, **`plannerApi.ts` / `types/index.ts`**, **`plannerEvents.ts`** as needed, and **integration/unit tests**.
3. **Security**: Navigation and URL tooling must remain consistent with **`UrlPolicy`** when adding URLs or fetch paths.
4. **Observability**: Planner uses **structlog**; prefer structured keys over ad-hoc print.
5. **Tests**: Add or extend **pytest** under `planner-service/app/tests/` or **Vitest** next to frontend services/components you change.

---

## 8. How to run locally

**Planner** (from `planner-service/`):

```bash
uv venv && uv pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

**Frontend** (from `frontend-ui/`):

```bash
npm install
npm run dev
```

**Tests**:

```bash
cd planner-service && pytest
cd frontend-ui && npm run test
```

---

## 9. Known documentation gaps / pitfalls

- `frontend-ui/Readme.md` may describe legacy endpoints; **`plannerApi.ts`** reflects the live `/agent/*` API — update readme if it diverges.
- `planner-service/pyproject.toml` references `readme = "README.md"` but the authored doc file is **`planner-service/readme.md`** — fix casing if packaging breaks on case-sensitive filesystems.

---

## 10. Quick “who do I edit?” routing

| Goal | Start here |
|------|------------|
| New agent behavior or tool | `planner/engine.py`, `planner/tools.py`, `schemas/tools.py`; browser executor contract §5.3 |
| New HTTP field or WS event type | `api/routes.py`, `schemas/`, frontend `types/` + `plannerEvents.ts` |
| UI flow / persistence of session id | `useAppStore.ts`, `plannerSessionStorage.ts` |
| Rate limits / CORS / env | `core/config.py`, `main.py` (app factory — open `planner-service/app/main.py`) |
| Prompt wording | `planner-service/app/prompts/*.md` |

When in doubt, read **`planner-service/readme.md`** and grep for existing patterns (`rg`, IDE search) before adding new layers or abstractions.

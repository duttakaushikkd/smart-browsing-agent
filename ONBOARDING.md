# Onboarding Manual: Smart Browsing Agent

Welcome! Use this onboarding document to understand the architecture, components, and development standards of the Smart Browsing Agent repository. Refer to this document before starting any implementation.

---

## 1. Project Overview

The Smart Browsing Agent is an AI-powered system designed to navigate websites and interact with them to achieve user goals. It splits operations across three main components:
1. **Frontend UI**: Next.js app serving as the chat interface, session tracker, and timeline viewer.
2. **Planner Service**: FastAPI backend coordinating the LLM planning loop, session status, tool execution calls, and client streams.
3. **MCP Tool Server**: Model Context Protocol server exposing browser automation and extraction tools.

---

## 2. Directory Structure & File Map

Here is the directory map with links to the corresponding files:

### Backend: Planner Service
- **App Entry Point**: [main.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/main.py) — Initializes FastAPI app, middlewares (CORS, Limiter), and component state.
- **Routing & Controllers**:
  - [routes.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/api/routes.py) — API endpoints (`/agent/start`, `/agent/{session_id}/continue`, etc.) and WebSocket streaming (`/agent/{session_id}/stream`).
  - [health.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/api/health.py) — Health check endpoint.
- **Agent Orchestration**:
  - [engine.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/planner/engine.py) — Coordinates the LLM execution loops, tool calls, and persistence.
  - [llm.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/planner/llm.py) — Interface for LLM initialization.
- **MCP Services & Client**:
  - [client.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/services/mcp_client/client.py) — MCP client wrapper communicating with the MCP tool server.
  - [circuit_breaker.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/services/circuit_breaker.py) — Resiliency pattern for remote client calls.
- **State & Memory Management**:
  - [store.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/memory/store.py) — Persistence wrappers for Session state (Redis or In-Memory).
  - [summarizer.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/memory/summarizer.py) — Condenses state details to manage context sizes.
- **Configuration**:
  - [config.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/planner-service/app/core/config.py) — Environment variables, default configuration parameters, and constraints.

### Tool Service: Model Context Protocol (MCP) Server
- **App Entry Point**: [main.py (mcp)](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/mcp/main.py) — Serves the MCP endpoints.
- **Executors & Registries**:
  - [app.py (server)](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/mcp/server/app.py) — Standalone FastAPI app for MCP.
  - [browser_actions.py](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/mcp/tools/browser_actions.py) — Low-level browser automation implementation definitions.

### Frontend: UI Dashboard
- **Entry & Layout**: [page.tsx](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/frontend-ui/src/app/page.tsx) and [layout.tsx](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/frontend-ui/src/app/layout.tsx).
- **Zustand State Store**: [useAppStore.ts](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/frontend-ui/src/store/useAppStore.ts) — Global client state (active sessions, connection statuses, UI logs).
- **Planner Interfaces**:
  - [plannerApi.ts](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/frontend-ui/src/services/plannerApi.ts) — API caller module wrapper.
  - [plannerSocket.ts](file:///Users/kaushikdutta/Documents/GitHub/smart-browsing-agent/frontend-ui/src/services/plannerSocket.ts) — Manages WebSocket connections and keep-alives.

---

## 3. High-Level System Architecture

```
+------------------+                   +--------------------+
|  Frontend UI     | <--- HTTP/WS ---> |  Planner Service   |
|  (Next.js App)   |                   |  (FastAPI Server)  |
+------------------+                   +---------+----------+
                                                 |
                                               HTTP
                                                 v
+------------------+                   +---------+----------+
| Browser Executor | <--- HTTP ------- |  MCP Tool Server   |
| (Ext Playwright) |                   |  (Tool Registry)   |
+------------------+                   +--------------------+
```

### Core Execution Flow
1. The **User** inputs a request/goal in the **Frontend UI**.
2. Frontend calls `POST /agent/start` to trigger a new session.
3. The **Planner Engine** initializes a loop:
   - Fetches available tools from the **MCP Tool Server**.
   - Asks the LLM (`openai`) to make the next logical step.
   - Executes the selected tool by calling the MCP Server.
   - Saves progress/history to the **Session Store**.
   - Pushes step outcomes/streams details back to the Frontend via the **WebSocket stream**.
4. The loop runs until the goal is accomplished or fails/reaches maximum steps.

---

## 4. Key Contracts & Protocols

### Planner HTTP Routes
- `POST /agent/start`
  - Body: `{ "goal": "string", "metadata": {} }`
  - Returns: `{ "session_id": "string", "state": "string" }`
- `POST /agent/{session_id}/continue`
  - Body: `{ "user_input": "string" }`
  - Returns: `AgentStatusResponse`
- `GET /agent/{session_id}/status`
  - Returns: Current timeline, token usage, and execution state.

### WebSockets Stream
- Endpoint: `/agent/{session_id}/stream`
- Yields live updates of active planner execution steps, screenshots, tool logs, and agent logs.

---

## 5. Local Setup & Execution Guide

### Starting Backend (Planner)
```bash
cd planner-service
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Starting Frontend UI
```bash
cd frontend-ui
npm install
npm run dev
```
Accessible at `http://localhost:3000`.

---

## 6. Implementation Principles & Guardrails

- **Minimalist Diffs**: Keep changes focused on the functional scope. Avoid refactoring unrelated components.
- **Contract Adherence**: Any edits to endpoint inputs or outputs must propagate to both `schemas/` in Python and `types/index.ts` / API service files in Next.js.
- **Structured Logging**: Use `structlog` for backend logging rather than generic print statements.
- **UrlPolicy Safety**: Ensure external navigations align with the defined `UrlPolicy` to restrict allowed domains.

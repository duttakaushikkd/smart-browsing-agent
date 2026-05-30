# Playwright Execution Service

A deterministic browser execution service built on FastAPI and Playwright, serving as the low-level automation layer for the Smart Browsing Agent.

---

## 1. System Architecture

```text
MCP Server --HTTP--> Playwright Service --Playwright API--> Headless Chrome
```

* **No Planning/LLMs**: Completely isolated, deterministic browser operations.
* **Isolated Sessions**: Separate browser contexts per `session_id`.
* **DOM Compression**: visible element filtering with accessibility tagging (`data-agent-ref`) to minimize context payload.

---

## 2. API Contract

### Session Management
* `POST /browser/session/create` -> returns `{ "session_id": "..." }`
* `POST /browser/session/close` -> accepts `{ "session_id": "..." }`
* `GET /browser/session/{id}/status` -> returns session status and open tabs.

### Page Actions
* `POST /browser/action`
  ```json
  {
    "session_id": "session-123",
    "action": "click_element",
    "payload": {
      "target_ref": "el:1"
    }
  }
  ```
  Returns:
  ```json
  {
    "success": true,
    "data": {
      "page_title": "Amazon",
      "current_url": "https://amazon.com",
      "visible_elements": []
    },
    "error": null,
    "metadata": {}
  }
  ```

---

## 3. How to Run Locally

```bash
cd playwright-service
pip install -e ".[dev]"
playwright install chromium
python main.py
```
Starts server on `http://localhost:8080`.
from typing import Any

import httpx
import pytest
import respx

from app.core.config import Settings
from app.memory.store import InMemorySessionStore
from app.memory.summarizer import MemorySummarizer
from app.planner.engine import PlannerEngine
from app.planner.llm import PlannerDecision, PlannerModel
from app.recovery.engine import RecoveryEngine
from app.schemas.state import AgentSession, AgentState
from app.services.mcp_client import McpClient, McpToolExecutor, ToolExecutionContext
from app.streaming.event_bus import EventBus


class OneToolThenFinishModel(PlannerModel):
    async def decide(self, session: AgentSession, tools: list[dict[str, Any]]) -> PlannerDecision:
        del tools
        if session.current_step == 0:
            return PlannerDecision(
                kind="tool",
                summary="Extract visible text",
                tool_name="extract_text",
                tool_args={},
            )
        return PlannerDecision(kind="finish", summary="done", final_result="done")


@pytest.mark.asyncio
@respx.mock
async def test_planner_invokes_remote_mcp_tool() -> None:
    respx.get("http://mcp:9000/v1/tools/schemas").mock(
        return_value=httpx.Response(200, json={"schemas": []})
    )
    respx.post("http://mcp:9000/v1/tools/call").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "success": True,
                    "data": {"text": "remote page text"},
                    "error": None,
                    "metadata": {},
                }
            },
        )
    )
    client = McpClient(
        base_url="http://mcp:9000",  # type: ignore[arg-type]
        timeout_seconds=5,
    )
    await client.get_tool_schemas(refresh=True)
    store = InMemorySessionStore()
    engine = PlannerEngine(
        settings=Settings(max_agent_steps=3, mcp_server_url="http://mcp:9000"),  # type: ignore[arg-type]
        store=store,
        model=OneToolThenFinishModel(),
        tool_executor=McpToolExecutor(client),
        events=EventBus(),
        summarizer=MemorySummarizer(),
        recovery=RecoveryEngine(),
    )
    session = await engine.start("extract text", {})
    await engine.run_until_blocked(session.session_id)
    stored = await store.get(session.session_id)
    await client.aclose()

    assert stored.state == AgentState.COMPLETED
    assert stored.observations[0].content == "remote page text"

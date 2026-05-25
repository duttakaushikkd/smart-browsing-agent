from typing import Any

import pytest

from app.core.config import Settings
from app.memory.store import InMemorySessionStore
from app.memory.summarizer import MemorySummarizer
from app.planner.engine import PlannerEngine
from app.planner.llm import PlannerDecision, PlannerModel
from app.planner.tools import Tool, ToolExecutionContext, ToolRegistry
from app.recovery.engine import RecoveryEngine
from app.schemas.state import AgentSession, AgentState
from app.schemas.tools import ToolResult
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


class ExtractTextTestTool(Tool[Any]):
    name = "extract_text"
    description = "test"
    args_model = type("EmptyArgs", (__import__("pydantic").BaseModel,), {})

    async def execute(self, context: ToolExecutionContext, arguments: Any) -> ToolResult:
        del context, arguments
        return ToolResult(success=True, data={"text": "page text"})


@pytest.mark.asyncio
async def test_planner_engine_runs_tool_and_finishes() -> None:
    store = InMemorySessionStore()
    engine = PlannerEngine(
        settings=Settings(max_agent_steps=3),
        store=store,
        model=OneToolThenFinishModel(),
        tool_registry=ToolRegistry([ExtractTextTestTool()]),
        events=EventBus(),
        summarizer=MemorySummarizer(),
        recovery=RecoveryEngine(),
    )

    session = await engine.start("extract text from current page", {})
    await engine.run_until_blocked(session.session_id)
    stored = await store.get(session.session_id)

    assert stored.state == AgentState.COMPLETED
    assert stored.action_history[0].tool_name == "extract_text"
    assert stored.observations[0].content == "page text"

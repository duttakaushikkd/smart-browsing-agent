import asyncio
from typing import Any
from uuid import uuid4

import structlog
from app.core.config import Settings
from app.memory.store import SessionStore
from app.memory.summarizer import MemorySummarizer
from app.planner.llm import PlannerModel
from app.services.mcp_client import ToolExecutionContext
from app.recovery.engine import RecoveryEngine
from app.schemas.events import StreamEvent, StreamEventType
from app.schemas.state import (
    ActionRecord,
    AgentSession,
    AgentState,
    ObservationRecord,
    SemanticElement,
)
from app.schemas.tools import ToolResult
from app.streaming.event_bus import EventBus
from app.services.mcp_client import McpToolExecutor

logger = structlog.get_logger(__name__)


class PlannerEngine:
    """State-aware planner loop that orchestrates LLM decisions and browser tools."""

    def __init__(
        self,
        settings: Settings,
        store: SessionStore,
        model: PlannerModel,
        tool_executor: McpToolExecutor,
        events: EventBus,
        summarizer: MemorySummarizer,
        recovery: RecoveryEngine,
    ) -> None:
        self._settings = settings
        self._store = store
        self._model = model
        self._tools = tool_executor
        self._events = events
        self._summarizer = summarizer
        self._recovery = recovery
        self._running_tasks: dict[str, asyncio.Task[None]] = {}

    async def start(self, goal: str, metadata: dict[str, Any]) -> AgentSession:
        session = AgentSession(
            session_id=str(uuid4()),
            goal=goal,
            max_steps=self._settings.max_agent_steps,
            metadata=metadata,
        )
        session.transition(AgentState.PLANNING, "Session started")
        await self._store.create(session)
        await self._emit(session, StreamEventType.STATE, "Session started")
        self._spawn(session.session_id)
        return session

    async def continue_session(self, session_id: str, user_input: str | None) -> AgentSession:
        session = await self._store.get(session_id)
        if user_input:
            session.goal = f"{session.goal}\nUser clarification: {user_input}"
        session.transition(AgentState.REPLANNING, "Continuing session")
        await self._store.save(session)
        await self._emit(session, StreamEventType.STATE, "Continuing session")
        self._spawn(session_id)
        return session

    async def cancel(self, session_id: str) -> AgentSession:
        session = await self._store.get(session_id)
        task = self._running_tasks.pop(session_id, None)
        if task:
            task.cancel()
        session.transition(AgentState.CANCELLED, "Session cancelled")
        await self._store.save(session)
        await self._emit(session, StreamEventType.COMPLETION, "Session cancelled")
        return session

    def _spawn(self, session_id: str) -> None:
        task = self._running_tasks.get(session_id)
        if task and not task.done():
            return
        self._running_tasks[session_id] = asyncio.create_task(self.run_until_blocked(session_id))

    async def run_until_blocked(self, session_id: str) -> None:
        try:
            while True:
                session = await self._store.get(session_id)
                if session.state in {
                    AgentState.WAITING_USER,
                    AgentState.COMPLETED,
                    AgentState.FAILED,
                    AgentState.CANCELLED,
                }:
                    return
                if session.current_step >= session.max_steps:
                    await self._fail(session, "Maximum planner steps reached")
                    return
                await asyncio.wait_for(
                    self._run_step(session),
                    timeout=self._settings.agent_step_timeout_seconds,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("planner_loop_failed", session_id=session_id)
            session = await self._store.get(session_id)
            await self._fail(session, str(exc))
        finally:
            self._running_tasks.pop(session_id, None)

    async def _run_step(self, session: AgentSession) -> None:
        session.transition(AgentState.PLANNING, "Planning next action")
        session.memory_summary = self._summarizer.summarize(session)
        await self._store.save(session)
        await self._emit(session, StreamEventType.PLAN, "Planning next action")

        recovery = self._recovery.evaluate(session)
        if recovery.should_recover and recovery.planner_decision:
            decision = recovery.planner_decision
            session.plan_summary = decision.summary
            await self._emit(
                session,
                StreamEventType.PLAN,
                decision.summary,
                {"recovery": True, "reason": recovery.reason},
            )
        else:
            decision = await self._model.decide(session, self._tools.openai_schemas())
        self._merge_usage(session, decision.usage or {})
        session.plan_summary = decision.summary

        if decision.kind == "clarification":
            session.transition(
                AgentState.WAITING_USER,
                decision.clarification_question or decision.summary,
            )
            await self._store.save(session)
            await self._emit(
                session,
                StreamEventType.STATE,
                session.state.value,
                {"question": decision.summary},
            )
            return

        if decision.kind == "finish":
            session.final_result = decision.final_result or decision.summary
            session.transition(AgentState.COMPLETED, "Goal completed")
            await self._store.save(session)
            await self._emit(
                session,
                StreamEventType.COMPLETION,
                "Goal completed",
                {"final_result": session.final_result},
            )
            return

        if not decision.tool_name:
            await self._fail(session, "Planner did not provide a tool name")
            return

        arguments = decision.tool_args or {}
        if self._is_looping(session, decision.tool_name, arguments):
            await self._fail(session, "Anti-loop protection triggered for repeated tool calls")
            return

        session.transition(
            AgentState.EXECUTING,
            f"Executing {decision.tool_name}",
            tool=decision.tool_name,
            arguments=arguments,
        )
        await self._store.save(session)
        await self._emit(
            session,
            StreamEventType.ACTION,
            decision.summary,
            {"tool": decision.tool_name, "arguments": arguments},
        )

        result = await self._execute_tool(session, decision.tool_name, arguments)
        session.current_step += 1
        session.action_history.append(
            ActionRecord(
                step=session.current_step,
                tool_name=decision.tool_name,
                arguments=arguments,
                success=result.success,
                summary=result.error or decision.summary,
            )
        )
        observation = self._observation_from_result(result)
        session.observations.append(
            ObservationRecord(
                step=session.current_step,
                content=observation,
                elements=self._elements_from_result(result),
                metadata=result.metadata | {"tool": decision.tool_name},
            )
        )
        session.transition(AgentState.OBSERVING, "Observed browser result")
        await self._store.save(session)
        await self._emit(
            session,
            StreamEventType.TOOL_RESULT,
            "Tool execution finished",
            result.model_dump(),
        )
        session.transition(AgentState.REPLANNING, "Replanning from observation")
        await self._store.save(session)

    async def _execute_tool(
        self,
        session: AgentSession,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        try:
            return await self._tools.execute(
                tool_name,
                arguments,
                ToolExecutionContext(session_id=session.session_id),
            )
        except Exception as exc:
            logger.exception("tool_execution_failed", session_id=session.session_id, tool=tool_name)
            return ToolResult(success=False, error=str(exc), metadata={"recoverable": True})

    def _observation_from_result(self, result: ToolResult) -> str:
        if result.success:
            if "text" in result.data:
                return str(result.data["text"])[:4000]
            return str(result.data)[:4000]
        return f"Tool failed: {result.error}"

    def _elements_from_result(self, result: ToolResult) -> list[SemanticElement]:
        raw_elements = result.data.get("elements", [])
        if not isinstance(raw_elements, list):
            return []
        elements: list[SemanticElement] = []
        for item in raw_elements[:100]:
            if isinstance(item, dict):
                try:
                    elements.append(SemanticElement.model_validate(item))
                except ValueError:
                    continue
        return elements

    def _is_looping(self, session: AgentSession, tool_name: str, arguments: dict[str, Any]) -> bool:
        recent = session.action_history[-3:]
        return len(recent) == 3 and all(
            item.tool_name == tool_name and item.arguments == arguments and not item.success
            for item in recent
        )

    def _merge_usage(self, session: AgentSession, usage: dict[str, int]) -> None:
        for key, value in usage.items():
            if isinstance(value, int):
                session.token_usage[key] = session.token_usage.get(key, 0) + value

    async def _fail(self, session: AgentSession, message: str) -> None:
        session.error = message
        session.transition(AgentState.FAILED, message)
        await self._store.save(session)
        await self._emit(session, StreamEventType.ERROR, message)

    async def _emit(
        self,
        session: AgentSession,
        event_type: StreamEventType,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        await self._events.publish(
            StreamEvent(
                session_id=session.session_id,
                type=event_type,
                state=session.state.name,
                step=session.current_step,
                message=message,
                payload=payload or {},
            )
        )

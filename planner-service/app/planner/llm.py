import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from openai import AsyncOpenAI

from app.core.config import Settings
from app.schemas.state import AgentSession

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


@dataclass(frozen=True, slots=True)
class PlannerDecision:
    kind: str
    summary: str
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    final_result: str | None = None
    clarification_question: str | None = None
    usage: dict[str, int] | None = None


class PlannerModel(Protocol):
    async def decide(self, session: AgentSession, tools: list[dict[str, Any]]) -> PlannerDecision:
        """Return the next planner decision."""


class OpenAIPlannerModel:
    """OpenAI SDK-compatible tool-calling planner."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._system_prompt = (PROMPT_DIR / "planner_system.md").read_text()

    async def decide(self, session: AgentSession, tools: list[dict[str, Any]]) -> PlannerDecision:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": (
                    f"Goal: {session.goal}\n"
                    f"State: {session.state.value}\n"
                    f"Step: {session.current_step}/{session.max_steps}\n"
                    f"Memory summary:\n{session.memory_summary or 'No prior observations.'}\n\n"
                    "Return a concise user-safe summary in normal assistant text. "
                    "Use a tool call for the next browser action, or finish/ask "
                    "clarification in text."
                ),
            },
        ]
        response = await self._client.chat.completions.create(
            model=self._settings.openai_model,
            messages=cast(Any, messages),
            tools=cast(Any, tools),
            tool_choice="auto",
            temperature=0.1,
        )
        choice = response.choices[0]
        message = choice.message
        usage = response.usage.model_dump() if response.usage else {}
        if message.tool_calls:
            tool_call = cast(Any, message.tool_calls[0])
            return PlannerDecision(
                kind="tool",
                summary=message.content or f"Calling {tool_call.function.name}",
                tool_name=tool_call.function.name,
                tool_args=json.loads(tool_call.function.arguments or "{}"),
                usage=usage,
            )
        content = message.content or ""
        lowered = content.lower()
        if "clarification" in lowered or "need you" in lowered or "please provide" in lowered:
            return PlannerDecision(
                kind="clarification",
                summary=content,
                clarification_question=content,
                usage=usage,
            )
        return PlannerDecision(kind="finish", summary=content, final_result=content, usage=usage)


class HeuristicPlannerModel:
    """Deterministic fallback for local tests when no API key is configured."""

    async def decide(self, session: AgentSession, tools: list[dict[str, Any]]) -> PlannerDecision:
        del tools
        if session.current_step == 0:
            words = session.goal.split()
            url = next((word for word in words if word.startswith(("http://", "https://"))), None)
            if url:
                return PlannerDecision(
                    kind="tool",
                    summary=f"Open {url}",
                    tool_name="open_url",
                    tool_args={"url": url},
                )
            return PlannerDecision(
                kind="clarification",
                summary="Please provide the website URL to start from.",
                clarification_question="Please provide the website URL to start from.",
            )
        if session.observations:
            return PlannerDecision(
                kind="finish",
                summary="Completed the available browser step.",
                final_result=session.observations[-1].content,
            )
        return PlannerDecision(
            kind="finish",
            summary="No further action is available.",
            final_result="",
        )


def create_planner_model(settings: Settings) -> PlannerModel:
    if settings.openai_api_key:
        return OpenAIPlannerModel(settings)
    return HeuristicPlannerModel()

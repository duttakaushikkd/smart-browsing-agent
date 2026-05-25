from dataclasses import dataclass

from app.planner.llm import PlannerDecision
from app.schemas.state import AgentSession


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    should_recover: bool
    reason: str | None = None
    planner_decision: PlannerDecision | None = None


class RecoveryEngine:
    """Autonomous recovery before failing a session."""

    def evaluate(self, session: AgentSession) -> RecoveryDecision:
        if not session.action_history:
            return RecoveryDecision(False)

        last = session.action_history[-1]
        last_observation = session.observations[-1] if session.observations else None
        failure_text = (
            f"{last.summary} {last_observation.content if last_observation else ''}".lower()
        )

        if last.success and last_observation and last_observation.content.strip():
            return RecoveryDecision(False)

        if last.retry_count >= 2:
            return RecoveryDecision(False, "Retry budget exhausted")

        if any(term in failure_text for term in ["target", "stale", "not found", "timeout"]):
            return RecoveryDecision(
                True,
                "Recovering from missing or stale element",
                PlannerDecision(
                    kind="tool",
                    summary="Refreshing the visible element summary before retrying.",
                    tool_name="get_dom_snapshot",
                    tool_args={"include_text": True},
                ),
            )

        if not last_observation or not last_observation.content.strip() or "empty" in failure_text:
            return RecoveryDecision(
                True,
                "Recovering from empty observation",
                PlannerDecision(
                    kind="tool",
                    summary="Requesting a screenshot artifact to inspect the current page state.",
                    tool_name="screenshot",
                    tool_args={"full_page": True},
                ),
            )

        if "navigation" in failure_text or "unexpected" in failure_text:
            return RecoveryDecision(
                True,
                "Recovering from unexpected navigation",
                PlannerDecision(
                    kind="tool",
                    summary="Going back to the previous browser state.",
                    tool_name="go_back",
                    tool_args={},
                ),
            )

        return RecoveryDecision(False)

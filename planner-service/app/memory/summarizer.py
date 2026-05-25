from app.schemas.state import AgentSession


class MemorySummarizer:
    """Token-efficient short-term memory summarizer.

    The production path can replace this deterministic summarizer with an LLM-backed
    summarizer while keeping the same interface.
    """

    def summarize(self, session: AgentSession, max_items: int = 8) -> str:
        actions = session.action_history[-max_items:]
        observations = session.observations[-max_items:]
        lines: list[str] = []
        if session.plan_summary:
            lines.append(f"Plan: {session.plan_summary}")
        for action in actions:
            status = "ok" if action.success else "failed"
            lines.append(f"Step {action.step}: {action.tool_name} {status}. {action.summary}")
        for observation in observations:
            compact = observation.content.replace("\n", " ")[:500]
            lines.append(f"Observation {observation.step}: {compact}")
        return "\n".join(lines)[-4000:]

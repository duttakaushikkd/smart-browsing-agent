from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentState(StrEnum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    REPLANNING = "replanning"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionRecord(BaseModel):
    step: int
    tool_name: str
    arguments: dict[str, Any]
    success: bool
    summary: str
    retry_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ObservationRecord(BaseModel):
    step: int
    content: str
    elements: list["SemanticElement"] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExecutionTimelineEvent(BaseModel):
    state: AgentState
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentSession(BaseModel):
    session_id: str
    goal: str
    state: AgentState = AgentState.IDLE
    current_step: int = 0
    max_steps: int = 20
    plan_summary: str | None = None
    final_result: str | None = None
    error: str | None = None
    action_history: list[ActionRecord] = Field(default_factory=list)
    observations: list[ObservationRecord] = Field(default_factory=list)
    timeline: list[ExecutionTimelineEvent] = Field(default_factory=list)
    memory_summary: str = ""
    token_usage: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    cancelled: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def transition(self, state: AgentState, message: str, **metadata: Any) -> None:
        self.state = state
        self.updated_at = datetime.now(UTC)
        self.timeline.append(
            ExecutionTimelineEvent(state=state, message=message, metadata=metadata)
        )


class SemanticElement(BaseModel):
    """Compressed, accessibility-tree-like browser observation element."""

    type: str
    text: str | None = None
    role: str | None = None
    target_ref: str | None = None
    visible: bool = True
    attributes: dict[str, str] = Field(default_factory=dict)


ObservationRecord.model_rebuild()

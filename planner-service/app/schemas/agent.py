from typing import Any

from pydantic import BaseModel, Field

from app.schemas.state import AgentState


class StartAgentRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContinueAgentRequest(BaseModel):
    user_input: str | None = Field(default=None, max_length=4000)


class AgentStartResponse(BaseModel):
    session_id: str
    state: AgentState


class AgentStatusResponse(BaseModel):
    session_id: str
    goal: str
    state: AgentState
    current_step: int
    plan_summary: str | None
    final_result: str | None
    error: str | None
    timeline: list[dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)


class CancelAgentResponse(BaseModel):
    session_id: str
    state: AgentState

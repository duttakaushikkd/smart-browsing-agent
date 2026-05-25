from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class StreamEventType(StrEnum):
    STATE = "state"
    PLAN = "plan"
    ACTION = "action"
    TOOL_RESULT = "tool_result"
    OBSERVATION = "observation"
    ERROR = "error"
    COMPLETION = "completion"


class StreamEvent(BaseModel):
    session_id: str
    event: str = "planner_update"
    type: StreamEventType
    state: str
    step: int
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

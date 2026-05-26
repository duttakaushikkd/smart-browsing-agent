from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from schemas.responses import ToolResult


class ToolExecutionContext(BaseModel):
    """Context passed to every tool execution."""

    session_id: str
    correlation_id: str | None = None


class BaseTool[ArgsT: BaseModel](ABC):
    """Generic async tool contract exposed by the MCP server."""

    name: str
    description: str
    input_schema: type[ArgsT]

    def openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema.model_json_schema(),
            },
        }

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema.model_json_schema(),
        }

    def validate_payload(self, payload: dict[str, Any]) -> ArgsT:
        return self.input_schema.model_validate(payload)

    @abstractmethod
    async def execute(self, context: ToolExecutionContext, payload: ArgsT) -> ToolResult:
        """Run the tool and return a normalized response envelope."""

from __future__ import annotations

from collections.abc import Iterable
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Any

from registry.base import BaseTool, ToolExecutionContext
from registry.exceptions import ToolRegistryConflictError, ToolUnavailableError
from schemas.api import ToolMetadata
from schemas.responses import ToolResult


class ToolRegistry:
    """Dynamic registry with schema introspection and runtime injection support."""

    def __init__(self, tools: Iterable[BaseTool[Any]] | None = None) -> None:
        self._tools: dict[str, BaseTool[Any]] = {}
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, tool: BaseTool[Any]) -> None:
        if tool.name in self._tools:
            raise ToolRegistryConflictError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> BaseTool[Any]:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolUnavailableError(f"Tool not found: {name}")
        return tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def list_metadata(self) -> list[ToolMetadata]:
        return [
            ToolMetadata(
                name=tool.name,
                description=tool.description,
                input_schema=tool.input_schema.model_json_schema(),
            )
            for tool in (self._tools[name] for name in self.names())
        ]

    def openai_schemas(self) -> list[dict[str, Any]]:
        return [self._tools[name].openai_schema() for name in self.names()]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        tool = self.get(name)
        validated = tool.validate_payload(arguments)
        return await tool.execute(context, validated)

    def autodiscover(self, package: str) -> None:
        module = import_module(package)
        for submodule in _iter_submodules(module):
            register = getattr(submodule, "register_tools", None)
            if callable(register):
                for tool in register():
                    self.register(tool)


def _iter_submodules(module: ModuleType) -> Iterable[ModuleType]:
    if not hasattr(module, "__path__"):
        return []
    discovered: list[ModuleType] = []
    for info in iter_modules(module.__path__, f"{module.__name__}."):
        discovered.append(import_module(info.name))
    return discovered

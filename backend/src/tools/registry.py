"""Pluggable tool registry — ported from agent platform."""

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: type[BaseModel]
    execute_fn: Callable[..., Any]


class ToolRegistry:
    """Registry for available tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def has_tool(self, name: str) -> bool:
        return name in self._tools


_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    return _registry

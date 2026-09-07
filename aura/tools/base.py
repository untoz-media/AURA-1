"""Core abstractions for safe AURA-1 tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    """Normalized result returned by a tool execution."""

    success: bool
    tool_name: str
    output: Any = None
    error: str | None = None

    @classmethod
    def ok(cls, tool_name: str, output: Any = None) -> "ToolResult":
        return cls(success=True, tool_name=tool_name, output=output)

    @classmethod
    def fail(cls, tool_name: str, error: str) -> "ToolResult":
        return cls(success=False, tool_name=tool_name, error=error)


@dataclass(frozen=True)
class Tool(ABC):
    """A named action that AURA can invoke through the tool registry."""

    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Execute the tool with validated keyword arguments."""
        raise NotImplementedError


class ToolRegistry:
    """Register, discover and safely execute AURA tools by explicit name."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool, rejecting empty or duplicate names."""
        name = tool.name.strip()
        if not name:
            raise ValueError("O nome da tool não pode estar vazio.")
        if name in self._tools:
            raise ValueError(f"Tool já registada: {name}")
        self._tools[name] = tool

    def get(self, name: str) -> Tool | None:
        """Return a registered tool by name."""
        return self._tools.get(name.strip())

    def list_tools(self) -> tuple[Tool, ...]:
        """Return registered tools in stable name order."""
        return tuple(self._tools[name] for name in sorted(self._tools))

    def run(self, name: str, **kwargs: Any) -> Any:
        """Execute one explicitly selected tool, preserving the raw result API."""
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool desconhecida: {name}")
        return tool.run(**kwargs)

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool and normalize expected and unexpected failures."""
        tool = self.get(name)
        if tool is None:
            return ToolResult.fail(name.strip(), f"Tool desconhecida: {name}")

        try:
            output = tool.run(**kwargs)
        except (TypeError, ValueError) as exc:
            return ToolResult.fail(tool.name, str(exc))
        except Exception:
            return ToolResult.fail(tool.name, "Ocorreu um erro inesperado ao executar a tool.")

        return ToolResult.ok(tool.name, output)

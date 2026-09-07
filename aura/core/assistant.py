"""AURA assistant orchestration layer."""

from __future__ import annotations

from aura.config import AuraConfig
from aura.memory.conversation import ConversationMemory
from aura.memory.persistent import MemoryEntry, PersistentMemory
from aura.model.qwen import QwenRuntime
from aura.settings import AuraSettings
from aura.tools import CalculatorTool, Tool, ToolRegistry, ToolResult


class AuraAssistant:
    """High-level AURA assistant interface."""

    def __init__(self, config: AuraConfig | None = None) -> None:
        self.settings = AuraSettings()
        self.config = config or self.settings.config()
        self.memory = ConversationMemory(max_messages=self.config.max_history_messages)
        self.persistent_memory = PersistentMemory()
        self.runtime = QwenRuntime(self.config)
        self.tools = ToolRegistry()
        self.register_tool(CalculatorTool())

    def chat(self, message: str) -> str:
        """Send one user message to AURA and return its response."""
        message = message.strip()
        if not message:
            raise ValueError("A mensagem não pode estar vazia.")

        self.memory.add_user(message)
        try:
            response = self.runtime.generate(self.memory.messages)
        except Exception:
            self.memory.messages.pop()
            raise

        self.memory.add_assistant(response)
        return response

    def register_tool(self, tool: Tool) -> None:
        """Register one tool available to the assistant."""
        self.tools.register(tool)

    def list_tools(self) -> tuple[Tool, ...]:
        """Return all registered tools."""
        return self.tools.list_tools()

    def run_tool(self, name: str, **kwargs):
        """Run one explicitly selected registered tool."""
        return self.tools.run(name, **kwargs)

    def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Safely execute one tool and return a normalized result."""
        return self.tools.execute(name, **kwargs)

    def remember(
        self,
        key: str,
        value: str,
        category: str = "general",
        importance: int = 3,
    ) -> None:
        """Store a user-approved structured persistent memory."""
        self.persistent_memory.set(key, value, category, importance)

    def recall(self, key: str) -> str | None:
        """Retrieve one memory value."""
        return self.persistent_memory.get(key)

    def recall_entry(self, key: str) -> MemoryEntry | None:
        """Retrieve one complete memory entry."""
        return self.persistent_memory.get_entry(key)

    def search_memory(self, query: str) -> dict[str, MemoryEntry]:
        """Search persistent memory."""
        return self.persistent_memory.search(query)

    def forget(self, key: str) -> bool:
        """Forget one memory."""
        return self.persistent_memory.delete(key)

    def clear_persistent_memory(self) -> None:
        """Clear all persistent memory entries."""
        self.persistent_memory.clear()

    def clear_memory(self) -> None:
        """Clear the current conversation history."""
        self.memory.clear()

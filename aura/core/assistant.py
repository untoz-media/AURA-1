"""AURA assistant orchestration layer."""

from __future__ import annotations

from aura.config import AuraConfig
from aura.memory.conversation import ConversationMemory
from aura.memory.persistent import PersistentMemory
from aura.model.qwen import QwenRuntime


class AuraAssistant:
    """High-level AURA assistant interface."""

    def __init__(self, config: AuraConfig | None = None) -> None:
        self.config = config or AuraConfig()
        self.memory = ConversationMemory(max_messages=self.config.max_history_messages)
        self.persistent_memory = PersistentMemory()
        self.runtime = QwenRuntime(self.config)

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

    def remember(self, key: str, value: str) -> None:
        """Store a user-approved persistent memory."""
        self.persistent_memory.set(key, value)

    def recall(self, key: str) -> str | None:
        """Retrieve one persistent memory entry."""
        return self.persistent_memory.get(key)

    def forget(self, key: str) -> bool:
        """Forget one persistent memory entry."""
        return self.persistent_memory.delete(key)

    def clear_persistent_memory(self) -> None:
        """Clear all persistent memory."""
        self.persistent_memory.clear()

    def clear_memory(self) -> None:
        """Clear the current conversation history."""
        self.memory.clear()

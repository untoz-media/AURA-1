"""AURA assistant orchestration layer."""

from __future__ import annotations

from aura.config import AuraConfig
from aura.memory.conversation import ConversationMemory
from aura.model.qwen import QwenRuntime


class AuraAssistant:
    """High-level AURA assistant interface."""

    def __init__(self, config: AuraConfig | None = None) -> None:
        self.config = config or AuraConfig()
        self.memory = ConversationMemory(max_messages=self.config.max_history_messages)
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

    def clear_memory(self) -> None:
        """Clear the current conversation history."""
        self.memory.clear()

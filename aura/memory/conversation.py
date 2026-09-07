"""Short-term conversation memory for AURA-1."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationMemory:
    """Keep the current conversation as chat-template messages."""

    messages: list[dict[str, str]] = field(default_factory=list)
    max_messages: int = 20

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self._trim()

    def clear(self) -> None:
        self.messages.clear()

    def _trim(self) -> None:
        if len(self.messages) > self.max_messages:
            self.messages[:] = self.messages[-self.max_messages :]

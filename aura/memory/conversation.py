"""Short-term conversation memory for AURA-1."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationMemory:
    """Keep the current conversation as ordered chat-template messages."""

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

    def recent(self) -> list[dict[str, str]]:
        """Return a copy of the current conversation in chronological order."""
        return list(self.messages)

    def _trim(self) -> None:
        if self.max_messages < 2:
            self.messages.clear()
            return

        if len(self.messages) > self.max_messages:
            limit = self.max_messages - (self.max_messages % 2)
            self.messages[:] = self.messages[-limit:]

        # Never leave an assistant message without its corresponding user turn.
        if self.messages and self.messages[0]["role"] != "user":
            self.messages.pop(0)

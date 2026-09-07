"""AURA assistant orchestration layer."""

from __future__ import annotations

from aura.config import AuraConfig
from aura.model.qwen import QwenRuntime


class AuraAssistant:
    """High-level AURA assistant interface."""

    def __init__(self, config: AuraConfig | None = None) -> None:
        self.config = config or AuraConfig()
        self.runtime = QwenRuntime(self.config)

    def chat(self, message: str) -> str:
        """Send one user message to AURA and return its response."""
        if not message.strip():
            raise ValueError("A mensagem não pode estar vazia.")
        return self.runtime.generate(message.strip())

"""Safe tool routing for AURA-1."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCall:
    """A validated tool call prepared for explicit execution."""

    tool_name: str
    arguments: dict[str, str]


class ToolRouter:
    """Detect a small set of safe tool intents without executing them."""

    _CALCULATOR = re.compile(r"^\s*(?:quanto é|quanto e|calcula|calcular|calculate)\s+(.+?)\s*\??$", re.IGNORECASE)
    _TIME = re.compile(r"^\s*(?:que horas são|que horas sao|que horas|hora atual|hora)\s*\??$", re.IGNORECASE)
    _DATE = re.compile(r"^\s*(?:que dia é hoje|que dia e hoje|data de hoje|data atual|qual é a data|qual e a data)\s*\??$", re.IGNORECASE)

    def route(self, message: str) -> ToolCall | None:
        """Return a tool call for a clearly recognized request, otherwise None."""
        text = message.strip()
        if not text:
            return None

        match = self._CALCULATOR.match(text)
        if match:
            expression = match.group(1).strip()
            if expression and self._looks_arithmetic(expression):
                return ToolCall("calculator", {"expression": expression})

        if self._TIME.match(text):
            return ToolCall("datetime", {"action": "time", "timezone": "Europe/Lisbon"})

        if self._DATE.match(text):
            return ToolCall("datetime", {"action": "date", "timezone": "Europe/Lisbon"})

        return None

    @staticmethod
    def _looks_arithmetic(expression: str) -> bool:
        """Allow only characters that can belong to our calculator syntax."""
        return bool(re.fullmatch(r"[0-9+\-*/%().\s]+", expression))

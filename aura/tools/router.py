"""Safe tool routing for AURA-1."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCall:
    """A validated tool call prepared for explicit execution."""

    tool_name: str
    arguments: dict[str, str]


class ToolRouter:
    """Detect a small set of safe tool intents without executing them."""

    _SYSTEM_INFO = re.compile(
        r"(?:quanta (?:memoria(?: ram)?|ram) tenho(?: disponivel)?|"
        r"how much (?:ram|memory) do i have(?: available)?|"
        r"how much (?:ram|memory) is available|"
        r"what (?:processor|cpu) do i have|"
        r"what (?:operating system|os) am i (?:using|running)|"
        r"(?:system|computer|pc) information|"
        r"qual (?:e )?a (?:minha )?(?:memoria ram|ram)(?: disponivel)?|"
        r"(?:que|qual) (?:e o meu )?(?:processador|cpu) tenho|"
        r"qual (?:e )?o meu (?:processador|cpu)|"
        r"quantos nucleos(?: logicos)? tenho|"
        r"que sistema operativo (?:tenho|estou a usar)|"
        r"qual (?:e )?o meu sistema operativo|"
        r"(?:informacao|informacoes) (?:do|sobre o) (?:sistema|meu pc|computador)|"
        r"system_info)"
    )

    _CALCULATOR = re.compile(
        r"^\s*(?:quanto é|quanto e|quanto dá|quanto da|calcula|calcular|faz|fazer|calculate)\s+(.+?)\s*\??$",
        re.IGNORECASE,
    )
    _TIME = re.compile(
        r"^\s*(?:que horas são|que horas sao|que horas|diz-me a hora|diz me a hora|hora atual|hora|what time is it|current time|time)\s*\??$",
        re.IGNORECASE,
    )
    _DATE = re.compile(
        r"^\s*(?:que dia é hoje|que dia e hoje|qual é a data|qual e a data|data de hoje|data atual|what is the date|what date is it|today'?s date|current date)\s*\??$",
        re.IGNORECASE,
    )

    def route(self, message: str) -> ToolCall | None:
        """Return a tool call for a clearly recognized request, otherwise None."""
        if not isinstance(message, str) or len(message) > 4096:
            return None
        text = message.strip()
        if not text:
            return None

        normalized = "".join(
            char for char in unicodedata.normalize("NFKD", text.lower())
            if not unicodedata.combining(char)
        )
        normalized = " ".join(normalized.rstrip("?!.").split())
        if self._SYSTEM_INFO.fullmatch(normalized):
            return ToolCall("system_info", {})

        if normalized in {"que ficheiros tenho nesta pasta", "lista os ficheiros", "lista os ficheiros nesta pasta"}:
            return ToolCall("files", {"action": "list", "path": "."})
        if normalized in {"what files are in this folder", "list files", "list the files", "list files in this folder"}:
            return ToolCall("files", {"action": "list", "path": "."})
        # Match the original text so that paths retain accents and case.
        for pattern, action in (
            (r"lista (?:os )?ficheiros (?:da|na) pasta\s+(.+?)\??", "list"),
            (r"existe (?:um |o )?ficheiro (?:chamado )?(.+?)\??", "exists"),
            (r"list (?:the )?files in (?:the )?folder\s+(.+?)\??", "list"),
            (r"does (?:the )?file\s+(.+?)\s+exist\??", "exists"),
        ):
            match = re.fullmatch(pattern, text, re.IGNORECASE)
            if match:
                path = match.group(1).strip()
                if len(path) >= 2 and path[0] == path[-1] and path[0] in "\"'":
                    path = path[1:-1]
                return ToolCall("files", {"action": action, "path": path})

        match = self._CALCULATOR.match(text)
        if match:
            expression = self._normalize_calculator_expression(match.group(1).strip())
            if expression and self._looks_arithmetic(expression):
                return ToolCall("calculator", {"expression": expression})

        if self._TIME.match(text):
            return ToolCall("datetime", {"action": "time", "timezone": "Europe/Lisbon"})

        if self._DATE.match(text):
            return ToolCall("datetime", {"action": "date", "timezone": "Europe/Lisbon"})

        return None

    @staticmethod
    def _normalize_calculator_expression(expression: str) -> str:
        """Convert a few natural arithmetic operators into calculator syntax."""
        normalized = expression.lower().strip().rstrip("?").strip()
        normalized = re.sub(r"\bvezes\b", "*", normalized)
        normalized = re.sub(r"\bdividido por\b", "/", normalized)
        normalized = re.sub(r"\bdividido\b", "/", normalized)
        normalized = re.sub(r"\bmais\b", "+", normalized)
        normalized = re.sub(r"\bmenos\b", "-", normalized)
        normalized = re.sub(r"\bpor cento de\b", "/100*", normalized)
        normalized = re.sub(r"\bpor cento\b", "/100", normalized)
        return normalized.strip()

    @staticmethod
    def _looks_arithmetic(expression: str) -> bool:
        """Allow only characters that can belong to our calculator syntax."""
        return bool(re.fullmatch(r"[0-9+\-*/%().\s]+", expression))

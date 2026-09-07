"""Date and time tool for AURA-1."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any

from aura.tools.base import Tool


class DateTimeTool(Tool):
    """Provide current date and time information."""

    def __init__(self) -> None:
        super().__init__(
            name="datetime",
            description="Returns the current date and time, including time zones.",
        )

    def run(self, action: str = "now", timezone: str = "Europe/Lisbon", **kwargs: Any) -> str:
        """Return the requested date/time information."""
        if kwargs or not isinstance(action, str) or not isinstance(timezone, str):
            raise ValueError("Indica apenas a ação e o fuso horário em texto.")
        action = action.strip().lower()
        if action not in {"now", "date", "time", "weekday", "timestamp"}:
            raise ValueError("Ação inválida. Usa now, date, time, weekday ou timestamp.")

        try:
            zone = ZoneInfo(timezone.strip())
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Fuso horário inválido.") from exc

        current = datetime.now(zone)

        if action == "now":
            return current.strftime("%d/%m/%Y %H:%M:%S (%Z)")
        if action == "date":
            return current.strftime("%d/%m/%Y")
        if action == "time":
            return current.strftime("%H:%M:%S")
        if action == "weekday":
            return current.strftime("%A")
        return str(int(current.timestamp()))

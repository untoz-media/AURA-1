"""Persistent local memory for AURA-1."""

from __future__ import annotations

import json
from pathlib import Path


class PersistentMemory:
    """Store small pieces of AURA-1 memory locally as JSON."""

    def __init__(self, path: str | Path = "data/memory/aura_memory.json") -> None:
        self.path = Path(path)
        self.data: dict[str, str] = {}
        self.load()

    def load(self) -> None:
        """Load memory from disk if it exists."""
        if not self.path.exists():
            self.data = {}
            return

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.data = {}
            return

        self.data = loaded if isinstance(loaded, dict) else {}

    def save(self) -> None:
        """Save memory to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def set(self, key: str, value: str) -> None:
        """Store or replace a memory entry."""
        self.data[key.strip()] = value.strip()
        self.save()

    def get(self, key: str) -> str | None:
        """Return one memory entry, if present."""
        return self.data.get(key.strip())

    def delete(self, key: str) -> bool:
        """Delete one memory entry and return whether it existed."""
        key = key.strip()
        if key not in self.data:
            return False
        del self.data[key]
        self.save()
        return True

    def clear(self) -> None:
        """Delete all persistent memory entries."""
        self.data.clear()
        self.save()

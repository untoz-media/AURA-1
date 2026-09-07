"""Persistent local memory for AURA-1."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    """One structured persistent memory entry."""

    value: str
    category: str = "general"
    importance: int = 3


class PersistentMemory:
    """Store structured AURA-1 memories locally as JSON."""

    VALID_CATEGORIES = {"general", "profile", "preference", "project", "fact"}

    def __init__(self, path: str | Path = "data/memory/aura_memory.json") -> None:
        self.path = Path(path)
        self.data: dict[str, MemoryEntry] = {}
        self.load()

    def load(self) -> None:
        """Load memory, including compatibility with the original key/value format."""
        if not self.path.exists():
            self.data = {}
            return

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.data = {}
            return

        if not isinstance(loaded, dict):
            self.data = {}
            return

        result: dict[str, MemoryEntry] = {}
        for key, value in loaded.items():
            if isinstance(value, str):
                result[str(key)] = MemoryEntry(value=value)
                continue
            if not isinstance(value, dict):
                continue
            memory_value = value.get("value")
            category = value.get("category", "general")
            importance = value.get("importance", 3)
            if not isinstance(memory_value, str):
                continue
            if not isinstance(category, str) or category not in self.VALID_CATEGORIES:
                category = "general"
            if not isinstance(importance, int) or isinstance(importance, bool):
                importance = 3
            result[str(key)] = MemoryEntry(
                value=memory_value,
                category=category,
                importance=max(1, min(5, importance)),
            )
        self.data = result

    def save(self) -> None:
        """Save memory to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: asdict(entry) for key, entry in self.data.items()}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def set(
        self,
        key: str,
        value: str,
        category: str = "general",
        importance: int = 3,
    ) -> None:
        """Store or replace one structured memory entry."""
        key = key.strip()
        category = category.strip().lower()
        if not key or not value.strip():
            raise ValueError("A chave e o valor da memória não podem estar vazios.")
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"Categoria inválida: {category}")
        if not isinstance(importance, int) or isinstance(importance, bool) or not 1 <= importance <= 5:
            raise ValueError("A importância deve ser um número entre 1 e 5.")
        self.data[key] = MemoryEntry(value=value.strip(), category=category, importance=importance)
        self.save()

    def get(self, key: str) -> str | None:
        """Return one memory value, if present."""
        entry = self.data.get(key.strip())
        return entry.value if entry else None

    def get_entry(self, key: str) -> MemoryEntry | None:
        """Return one complete memory entry, if present."""
        return self.data.get(key.strip())

    def search(self, query: str) -> dict[str, MemoryEntry]:
        """Find memories whose key, value, or category contains the query."""
        query = query.strip().lower()
        if not query:
            return dict(self.data)
        return {
            key: entry
            for key, entry in self.data.items()
            if query in key.lower()
            or query in entry.value.lower()
            or query in entry.category.lower()
        }

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

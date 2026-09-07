"""User-facing settings for AURA-1."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from aura.config import AuraConfig


class AuraSettings:
    """Load and save AURA-1 runtime settings as local JSON."""

    def __init__(self, path: str | Path = "data/settings/aura_settings.json") -> None:
        self.path = Path(path)
        self.data = asdict(AuraConfig())
        self.load()

    def load(self) -> None:
        """Load valid user settings, keeping safe defaults for missing values."""
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(loaded, dict):
            for key in self.data:
                if key in loaded and isinstance(loaded[key], type(self.data[key])):
                    self.data[key] = loaded[key]

    def save(self) -> None:
        """Persist the current settings locally."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reset(self) -> None:
        """Restore the default AURA-1 configuration."""
        self.data = asdict(AuraConfig())
        self.save()

    def get(self, key: str):
        """Return one setting by name."""
        return self.data.get(key)

    def set(self, key: str, value) -> bool:
        """Set one known setting, returning whether the key exists."""
        if key not in self.data:
            return False
        self.data[key] = value
        self.save()
        return True

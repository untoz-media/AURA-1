"""User-facing settings for AURA-1."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from aura.config import AuraConfig
from aura.profiles import apply_profile


class AuraSettings:
    """Load and save AURA-1 runtime settings as local JSON."""

    SCHEMA_VERSION = 2

    def __init__(self, path: str | Path = "data/settings/aura_settings.json") -> None:
        self.path = Path(path)
        self.data: dict[str, Any] = asdict(AuraConfig())
        self.active_profile = "balanced"
        self.load()

    def load(self) -> None:
        """Load user settings, keeping defaults for missing or invalid values."""
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(loaded, dict):
            return
        loaded_version = loaded.get("_settings_version", 1)
        for key, default in self.data.items():
            # Version 2 changes the product's primary language and base prompt.
            if loaded_version < 2 and key in {"language", "system_prompt"}:
                continue
            value = loaded.get(key)
            if type(value) is type(default):
                self.data[key] = value
        profile = loaded.get("active_profile")
        if isinstance(profile, str) and profile in {"fast", "balanced", "deep"}:
            self.active_profile = profile

    def save(self) -> None:
        """Persist the current settings locally."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {**self.data, "active_profile": self.active_profile, "_settings_version": self.SCHEMA_VERSION}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def reset(self) -> None:
        """Restore the default AURA-1 configuration."""
        self.data = asdict(AuraConfig())
        self.active_profile = "balanced"
        self.save()

    def get(self, key: str) -> Any:
        """Return one setting by name."""
        return self.data.get(key)

    def set(self, key: str, value: Any) -> bool:
        """Set one known setting, returning whether the key exists."""
        if key not in self.data or type(value) is not type(self.data[key]):
            return False
        self.data[key] = value
        self.save()
        return True

    def set_profile(self, profile: str) -> bool:
        """Select a runtime profile and persist it."""
        profile = profile.lower().strip()
        if profile not in {"fast", "balanced", "deep"}:
            return False
        self.active_profile = profile
        self.save()
        return True

    def config(self) -> AuraConfig:
        """Build the runtime config with the active profile applied."""
        return apply_profile(AuraConfig(**self.data), self.active_profile)

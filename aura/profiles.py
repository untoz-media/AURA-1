"""Runtime profiles for AURA-1."""

from __future__ import annotations

from dataclasses import replace

from aura.config import AuraConfig


PROFILES: dict[str, dict[str, object]] = {
    "fast": {
        "max_new_tokens": 160,
        "temperature": 0.5,
        "top_p": 0.8,
        "repetition_penalty": 1.05,
        "enable_thinking": False,
    },
    "balanced": {
        "max_new_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.8,
        "repetition_penalty": 1.05,
        "enable_thinking": False,
    },
    "deep": {
        "max_new_tokens": 512,
        "temperature": 0.6,
        "top_p": 0.9,
        "repetition_penalty": 1.05,
        "enable_thinking": True,
    },
}


PROFILE_LABELS = {
    "fast": "⚡ Fast",
    "balanced": "⚖️ Balanced",
    "deep": "🧠 Deep",
}


def available_profiles() -> tuple[str, ...]:
    """Return the available profile names."""
    return tuple(PROFILES)


def apply_profile(config: AuraConfig, profile: str) -> AuraConfig:
    """Return a config with the selected profile applied."""
    profile = profile.lower().strip()
    if profile not in PROFILES:
        raise ValueError(f"Perfil desconhecido: {profile}")
    return replace(config, **PROFILES[profile])

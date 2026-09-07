"""Settings defaults and language migration."""

import json

from aura.settings import AuraSettings


def test_english_is_primary_default(tmp_path):
    settings = AuraSettings(tmp_path / "missing.json")
    assert settings.config().language == "en"
    assert "Use English by default" in settings.config().system_prompt


def test_legacy_language_and_prompt_are_migrated(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({
        "language": "pt-PT",
        "system_prompt": "És AURA-1, legacy prompt",
        "temperature": 0.5,
        "active_profile": "deep",
    }), encoding="utf-8")
    settings = AuraSettings(path)
    assert settings.config().language == "en"
    assert "Use English by default" in settings.config().system_prompt
    assert settings.data["temperature"] == 0.5
    assert settings.active_profile == "deep"

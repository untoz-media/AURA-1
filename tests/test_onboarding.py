"""First-run onboarding and hardware compatibility tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from aura.onboarding import OnboardingManager


class FakeSettings:
    selected: list[str] = []

    def set_profile(self, profile: str) -> bool:
        self.selected.append(profile)
        return profile in {"fast", "balanced", "deep"}


def memory(total_gb: float, available_gb: float):
    return SimpleNamespace(
        total=int(total_gb * 1024**3),
        available=int(available_gb * 1024**3),
    )


def disk(free_gb: float):
    return SimpleNamespace(
        total=int(500 * 1024**3),
        used=int((500 - free_gb) * 1024**3),
        free=int(free_gb * 1024**3),
    )


def test_first_run_starts_incomplete(tmp_path):
    manager = OnboardingManager(tmp_path / "first_run.json", settings_factory=FakeSettings)
    state = manager.public_state()
    assert manager.completed is False
    assert state["profile"] == "balanced"
    assert {item["id"] for item in state["profiles"]} == {"fast", "balanced", "deep"}


def test_complete_persists_profile_and_consent(tmp_path):
    FakeSettings.selected.clear()
    path = tmp_path / "first_run.json"
    manager = OnboardingManager(path, settings_factory=FakeSettings)
    manager.complete(
        profile="fast",
        privacy_acknowledged=True,
        permission_boundary_acknowledged=True,
    )
    assert manager.completed is True
    assert FakeSettings.selected == ["fast"]

    restored = OnboardingManager(path, settings_factory=FakeSettings)
    assert restored.completed is True
    assert restored.profile == "fast"
    assert restored.data["privacy_acknowledged"] is True
    assert restored.data["permission_boundary_acknowledged"] is True
    assert isinstance(restored.data["completed_at"], str)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile": "turbo", "privacy_acknowledged": True, "permission_boundary_acknowledged": True},
        {"profile": "balanced", "privacy_acknowledged": False, "permission_boundary_acknowledged": True},
        {"profile": "balanced", "privacy_acknowledged": True, "permission_boundary_acknowledged": False},
    ],
)
def test_setup_rejects_invalid_or_missing_acknowledgements(tmp_path, kwargs):
    manager = OnboardingManager(tmp_path / "first_run.json", settings_factory=FakeSettings)
    with pytest.raises(ValueError):
        manager.complete(**kwargs)
    assert manager.completed is False


def test_hardware_ready_baseline(monkeypatch, tmp_path):
    manager = OnboardingManager(tmp_path / "first_run.json", settings_factory=FakeSettings)
    monkeypatch.setattr("aura.onboarding.psutil.virtual_memory", lambda: memory(16, 10))
    monkeypatch.setattr("aura.onboarding.shutil.disk_usage", lambda _path: disk(120))
    monkeypatch.setattr("aura.onboarding.platform.system", lambda: "Windows")
    monkeypatch.setattr("aura.onboarding.platform.release", lambda: "11")
    monkeypatch.setattr("aura.onboarding.platform.machine", lambda: "AMD64")
    monkeypatch.setattr("aura.onboarding.os.cpu_count", lambda: 12)
    monkeypatch.setattr(
        manager,
        "_gpu_info",
        lambda: {"available": True, "name": "Test GPU", "vram_gb": 4.0, "backend": "cuda"},
    )
    result = manager.hardware_check()
    assert result["status"] == "ready"
    assert result["can_continue"] is True
    assert result["cpu_logical"] == 12
    assert result["gpu"]["name"] == "Test GPU"
    assert result["blockers"] == []


def test_hardware_limited_can_continue(monkeypatch, tmp_path):
    manager = OnboardingManager(tmp_path / "first_run.json", settings_factory=FakeSettings)
    monkeypatch.setattr("aura.onboarding.psutil.virtual_memory", lambda: memory(12, 5))
    monkeypatch.setattr("aura.onboarding.shutil.disk_usage", lambda _path: disk(15))
    monkeypatch.setattr("aura.onboarding.platform.system", lambda: "Windows")
    monkeypatch.setattr(manager, "_gpu_info", lambda: {"available": False, "name": None, "vram_gb": None, "backend": "cpu"})
    result = manager.hardware_check()
    assert result["status"] == "limited"
    assert result["can_continue"] is True
    assert result["warnings"]


def test_hardware_below_minimum_blocks_model_setup(monkeypatch, tmp_path):
    manager = OnboardingManager(tmp_path / "first_run.json", settings_factory=FakeSettings)
    monkeypatch.setattr("aura.onboarding.psutil.virtual_memory", lambda: memory(4, 2))
    monkeypatch.setattr("aura.onboarding.shutil.disk_usage", lambda _path: disk(6))
    monkeypatch.setattr("aura.onboarding.platform.system", lambda: "Windows")
    monkeypatch.setattr(manager, "_gpu_info", lambda: {"available": False, "name": None, "vram_gb": None, "backend": "cpu"})
    result = manager.hardware_check()
    assert result["status"] == "unsupported"
    assert result["can_continue"] is False
    assert len(result["blockers"]) == 2


def test_reset_returns_to_first_run(tmp_path):
    path = tmp_path / "first_run.json"
    manager = OnboardingManager(path, settings_factory=FakeSettings)
    manager.complete(
        profile="deep",
        privacy_acknowledged=True,
        permission_boundary_acknowledged=True,
    )
    manager.reset()
    assert manager.completed is False
    assert manager.data["privacy_acknowledged"] is False
    assert manager.data["permission_boundary_acknowledged"] is False

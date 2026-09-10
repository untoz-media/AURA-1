"""Deep read-only system-awareness tests for AURA-1 Alpha 2."""

from types import SimpleNamespace

import aura.tools.system_state as system_state_module
from aura.tools.system_state import SystemStateResult, SystemStateTool


class FakeProcess:
    def __init__(self, pid, name, memory_mb):
        self.info = {
            "pid": pid,
            "name": name,
            "memory_info": SimpleNamespace(
                rss=int(memory_mb * 1024 * 1024),
            ),
        }


def patch_psutil(monkeypatch, *, cpu=42.5, ram_percent=61.0, battery=True):
    monkeypatch.setattr(
        system_state_module.psutil,
        "cpu_percent",
        lambda interval=None: cpu,
    )
    monkeypatch.setattr(
        system_state_module.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(
            total=16 * 1024 ** 3,
            used=10 * 1024 ** 3,
            available=6 * 1024 ** 3,
            percent=ram_percent,
        ),
    )
    monkeypatch.setattr(
        system_state_module.psutil,
        "process_iter",
        lambda _fields: [
            FakeProcess(3, "small.exe", 100),
            FakeProcess(1, "largest.exe", 1800),
            FakeProcess(2, "medium.exe", 700),
        ],
    )

    if battery:
        monkeypatch.setattr(
            system_state_module.psutil,
            "sensors_battery",
            lambda: SimpleNamespace(
                percent=73.0,
                power_plugged=False,
                secsleft=3600,
            ),
        )
    else:
        monkeypatch.setattr(
            system_state_module.psutil,
            "sensors_battery",
            lambda: None,
        )


def test_snapshot_returns_bounded_structured_telemetry(monkeypatch):
    patch_psutil(monkeypatch)
    monkeypatch.setattr(
        SystemStateTool,
        "_foreground_process_name",
        staticmethod(lambda: "obs64.exe"),
    )

    result = SystemStateTool().snapshot()

    assert isinstance(result, SystemStateResult)
    assert result["sucesso"] is True
    assert result["cpu_percent"] == 42.5
    assert result["ram"]["total_gb"] == 16.0
    assert result["ram"]["disponivel_gb"] == 6.0
    assert result["bateria"]["percentagem"] == 73.0
    assert result["foreground_app"] == "obs64.exe"
    assert result["processos_memoria"][0]["nome"] == "largest.exe"
    assert len(result["processos_memoria"]) <= SystemStateTool.TOP_PROCESS_LIMIT
    assert "Estado do PC" in str(result)


def test_high_resource_use_is_reported_but_never_as_an_action(monkeypatch):
    patch_psutil(monkeypatch, cpu=93.0, ram_percent=91.0)
    monkeypatch.setattr(
        SystemStateTool,
        "_foreground_process_name",
        staticmethod(lambda: None),
    )

    result = SystemStateTool().snapshot()

    assert result["pressao"] == "high"
    assert "fechar" not in result
    assert "kill" not in result
    assert "command" not in result


def test_snapshot_omits_sensitive_window_and_process_metadata(monkeypatch):
    patch_psutil(monkeypatch)
    monkeypatch.setattr(
        SystemStateTool,
        "_foreground_process_name",
        staticmethod(lambda: "brave.exe"),
    )

    result = SystemStateTool().snapshot()
    serialized_keys = set(result)

    assert "window_title" not in serialized_keys
    assert "clipboard" not in serialized_keys
    assert "username" not in serialized_keys
    assert "cmdline" not in serialized_keys
    assert all(
        set(process).issubset({"pid", "nome", "memoria_mb"})
        for process in result["processos_memoria"]
    )


def test_desktop_without_battery_is_supported(monkeypatch):
    patch_psutil(monkeypatch, battery=False)
    monkeypatch.setattr(
        SystemStateTool,
        "_foreground_process_name",
        staticmethod(lambda: None),
    )

    result = SystemStateTool().snapshot()

    assert result["sucesso"] is True
    assert result["bateria"] is None
    assert "bateria:" not in str(result)


def test_pressure_thresholds_are_deterministic():
    assert SystemStateTool._pressure_level(20.0, 40.0) == "normal"
    assert SystemStateTool._pressure_level(65.0, 40.0) == "moderate"
    assert SystemStateTool._pressure_level(20.0, 70.0) == "moderate"
    assert SystemStateTool._pressure_level(85.0, 40.0) == "high"
    assert SystemStateTool._pressure_level(20.0, 85.0) == "high"

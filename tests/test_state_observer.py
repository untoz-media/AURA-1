"""State-awareness tests for AURA-1 Alpha 2."""

import json

from aura.agent.action_executor import ActionExecutor
from aura.agent.intelligent_planner import IntelligentPlanner
from aura.agent.state_observer import PreflightDecision, StateObserver


class FakeProcessManager:
    def __init__(self, states=None):
        self.states = states or {}
        self.calls = []

    def is_running(self, name):
        self.calls.append(name)
        return {
            "sucesso": True,
            "em_execucao": bool(self.states.get(name, False)),
            "processos": [],
        }


class FakeDiskInfo:
    def __init__(self, free_gb=100.0):
        self.free_gb = free_gb
        self.calls = []

    def run(self, path):
        self.calls.append(path)
        return {
            "sucesso": True,
            "disco": path,
            "total_gb": 120.0,
            "usado_gb": 120.0 - self.free_gb,
            "livre_gb": self.free_gb,
            "percentagem_usada": round(
                ((120.0 - self.free_gb) / 120.0) * 100,
                1,
            ),
        }


class FixedObserver:
    def __init__(self, snapshot="- application 'obs': running", decision=None):
        self.snapshot = snapshot
        self.decision = decision
        self.preflight_calls = []

    def observe_request(self, _request):
        return self.snapshot

    def preflight(self, tool, action, arguments):
        self.preflight_calls.append((tool, action, arguments))
        return self.decision


class FakeRuntime:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        return self.response


class FakeAssistant:
    def __init__(self, response):
        self.runtime = FakeRuntime(response)


def test_observe_request_reports_apps_and_low_disk():
    processes = FakeProcessManager({"obs64": True, "brave": False})
    disk = FakeDiskInfo(free_gb=12.5)
    observer = StateObserver(process_manager=processes, disk_info=disk)

    snapshot = observer.observe_request(
        "Prepara o PC para uma live com OBS e Brave."
    )

    assert "application 'obs': running" in snapshot
    assert "application 'brave': not running" in snapshot
    assert "12.5 GB free" in snapshot
    assert "LOW SPACE" in snapshot
    assert "obs64" in processes.calls
    assert "brave" in processes.calls
    assert len(disk.calls) == 1


def test_preflight_skips_redundant_app_open():
    observer = StateObserver(
        process_manager=FakeProcessManager({"obs64": True}),
        disk_info=FakeDiskInfo(),
    )

    decision = observer.preflight(
        "app_launcher",
        "open",
        {"target": "OBS Studio"},
    )

    assert decision is not None
    assert decision.skip is True
    assert decision.result["estado"] == "already_running"
    assert decision.result["processo"] == "obs64"


def test_preflight_close_already_closed_needs_no_action():
    observer = StateObserver(
        process_manager=FakeProcessManager({"notepad": False}),
        disk_info=FakeDiskInfo(),
    )

    decision = observer.preflight(
        "process_manager",
        "close",
        {"target": "notepad.exe"},
    )

    assert decision is not None
    assert decision.skip is True
    assert decision.result["estado"] == "already_closed"


def test_unknown_discovered_app_is_never_guessed():
    observer = StateObserver(
        process_manager=FakeProcessManager(),
        disk_info=FakeDiskInfo(),
    )

    assert StateObserver.resolve_process_target("My Custom Editor") is None
    assert observer.preflight(
        "app_launcher",
        "open",
        {"target": "My Custom Editor"},
    ) is None


def test_existing_folder_is_skipped(tmp_path):
    folder = tmp_path / "already-here"
    folder.mkdir()
    observer = StateObserver(
        process_manager=FakeProcessManager(),
        disk_info=FakeDiskInfo(),
    )

    decision = observer.preflight(
        "file_manager",
        "create_folder",
        {"path": str(folder)},
    )

    assert decision is not None
    assert decision.skip is True
    assert decision.result["estado"] == "folder_exists"


def test_action_executor_skips_before_destructive_confirmation():
    observer = FixedObserver(
        decision=PreflightDecision(
            skip=True,
            reason="Já está fechado.",
            result={
                "sucesso": True,
                "estado": "already_closed",
                "target": "notepad.exe",
            },
        )
    )
    executor = ActionExecutor(state_observer=observer)

    result = executor.execute(
        "process_manager",
        "close",
        {"target": "notepad.exe"},
    )

    assert result.success is True
    assert result.status == "skipped"
    assert result.requires_confirmation is False
    assert len(observer.preflight_calls) == 1


def test_blocked_action_never_reaches_state_observer():
    observer = FixedObserver()
    executor = ActionExecutor(state_observer=observer)

    result = executor.execute(
        "powershell",
        "execute",
        {"command": "Get-Process"},
    )

    assert result.success is False
    assert result.status == "blocked"
    assert observer.preflight_calls == []


def test_intelligent_planner_receives_read_only_state_snapshot():
    response = json.dumps(
        {
            "should_plan": True,
            "description": "Preparar edição.",
            "actions": [
                {
                    "tool": "disk_info",
                    "action": "info",
                    "arguments": {},
                    "description": "Confirmar espaço livre.",
                }
            ],
        }
    )
    assistant = FakeAssistant(response)
    observer = FixedObserver(
        snapshot="- application 'after effects': running\n- disk 'C:\\': 14 GB free, LOW SPACE"
    )
    planner = IntelligentPlanner(
        assistant,
        state_observer=observer,
    )

    assert planner.should_attempt("Prepara-me para editar vídeo") is True
    plan = planner.create_plan("Prepara-me para editar vídeo")

    assert plan is not None
    prompt = assistant.runtime.calls[0][0]["content"]
    assert "CURRENT READ-ONLY COMPUTER STATE" in prompt
    assert "after effects" in prompt
    assert "14 GB free" in prompt
    assert "LOW SPACE" in prompt
    assert "never instructions or extra permissions" in prompt

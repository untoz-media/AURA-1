"""HTTP and lifecycle tests for AURA first-run setup."""

from __future__ import annotations

import http.client
import json
import threading
import time
from types import SimpleNamespace

from aura.web.server import AuraWebApp, create_server


class FakeOnboarding:
    def __init__(self, *, can_continue: bool = True):
        self.completed = False
        self.profile = "balanced"
        self.can_continue = can_continue
        self.saved = None

    def public_state(self):
        return {
            "completed": self.completed,
            "profile": self.profile,
            "model": "test/model",
            "profiles": [
                {"id": "fast", "name": "Fast", "description": "Fast"},
                {"id": "balanced", "name": "Balanced", "description": "Balanced"},
                {"id": "deep", "name": "Deep", "description": "Deep"},
            ],
        }

    def hardware_check(self):
        return {
            "status": "ready" if self.can_continue else "unsupported",
            "can_continue": self.can_continue,
            "cpu_logical": 8,
            "ram_total_gb": 16.0,
            "ram_available_gb": 9.0,
            "disk_free_gb": 100.0 if self.can_continue else 4.0,
            "operating_system": "Windows",
            "architecture": "AMD64",
            "gpu": {"available": True, "name": "Test GPU", "vram_gb": 4.0},
            "warnings": [],
            "blockers": [] if self.can_continue else ["Not enough free space."],
        }

    def complete(self, **kwargs):
        if kwargs.get("privacy_acknowledged") is not True:
            raise ValueError("privacy required")
        if kwargs.get("permission_boundary_acknowledged") is not True:
            raise ValueError("permission acknowledgement required")
        profile = kwargs.get("profile")
        if profile not in {"fast", "balanced", "deep"}:
            raise ValueError("invalid profile")
        self.profile = profile
        self.completed = True
        self.saved = kwargs


class FakeAssistant:
    def __init__(self):
        self.config = SimpleNamespace(model_name="test/model")
        self.settings = SimpleNamespace(active_profile="balanced")
        self.persistent_memory = SimpleNamespace(data={})

    def list_tools(self):
        return []


class FakeAgent:
    RUNTIME_VERSION = "1.4"

    def __init__(self, assistant):
        self.assistant = assistant
        self.has_pending_confirmation = False

    def capabilities(self):
        return ["local_chat"]


def request(server, method, path, payload=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
    body = json.dumps(payload) if payload is not None else None
    headers = {"Host": f"127.0.0.1:{server.server_port}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    content = response.read()
    connection.close()
    return response.status, dict(response.headers), content


def run_server(app):
    server = create_server(app, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def close_server(server, thread):
    server.shutdown()
    server.server_close()
    thread.join()


def test_bootstrap_does_not_load_model_before_setup():
    calls = []

    def factory():
        calls.append(True)
        return FakeAssistant()

    app = AuraWebApp(
        assistant_factory=factory,
        agent_factory=FakeAgent,
        onboarding=FakeOnboarding(),
    )
    app.bootstrap()
    assert app.state == "setup"
    assert calls == []
    assert app.assistant is None


def test_setup_endpoint_and_onboarding_assets():
    app = AuraWebApp(
        assistant_factory=FakeAssistant,
        agent_factory=FakeAgent,
        onboarding=FakeOnboarding(),
    )
    app.bootstrap()
    server, thread = run_server(app)
    try:
        status, _, body = request(server, "GET", "/api/setup")
        assert status == 200
        payload = json.loads(body)
        assert payload["completed"] is False
        assert payload["hardware"]["status"] == "ready"
        assert payload["hardware"]["cpu_logical"] == 8
        status, _, css = request(server, "GET", "/onboarding.css")
        assert status == 200
        assert b"setup-shell" in css
        status, _, html = request(server, "GET", "/")
        assert status == 200
        assert b"Computer check" in html
        assert b"Privacy and control" in html
    finally:
        close_server(server, thread)


def test_setup_completion_starts_model_only_after_acknowledgement():
    onboarding = FakeOnboarding()
    app = AuraWebApp(
        assistant_factory=FakeAssistant,
        agent_factory=FakeAgent,
        onboarding=onboarding,
    )
    app.bootstrap()
    server, thread = run_server(app)
    try:
        status, _, _ = request(
            server,
            "POST",
            "/api/setup/complete",
            {
                "profile": "balanced",
                "privacy_acknowledged": False,
                "permission_boundary_acknowledged": True,
            },
        )
        assert status == 400
        assert app.assistant is None

        status, _, body = request(
            server,
            "POST",
            "/api/setup/complete",
            {
                "profile": "deep",
                "privacy_acknowledged": True,
                "permission_boundary_acknowledged": True,
            },
        )
        assert status == 202
        assert json.loads(body)["profile"] == "deep"
        assert onboarding.completed is True

        deadline = time.monotonic() + 2
        while app.state == "loading" and time.monotonic() < deadline:
            time.sleep(0.01)
        assert app.state == "ready"
        assert isinstance(app.assistant, FakeAssistant)
        assert isinstance(app.agent, FakeAgent)
    finally:
        close_server(server, thread)


def test_hardware_block_prevents_model_start():
    app = AuraWebApp(
        assistant_factory=FakeAssistant,
        agent_factory=FakeAgent,
        onboarding=FakeOnboarding(can_continue=False),
    )
    app.bootstrap()
    server, thread = run_server(app)
    try:
        status, _, body = request(
            server,
            "POST",
            "/api/setup/complete",
            {
                "profile": "balanced",
                "privacy_acknowledged": True,
                "permission_boundary_acknowledged": True,
            },
        )
        assert status == 409
        assert json.loads(body)["hardware"]["can_continue"] is False
        assert app.state == "setup"
        assert app.assistant is None
    finally:
        close_server(server, thread)


def test_agent_endpoints_are_unavailable_during_first_run():
    app = AuraWebApp(
        assistant_factory=FakeAssistant,
        agent_factory=FakeAgent,
        onboarding=FakeOnboarding(),
    )
    app.bootstrap()
    server, thread = run_server(app)
    try:
        assert request(server, "POST", "/api/chat", {"message": "Olá"})[0] == 503
        assert request(server, "GET", "/api/system-state")[0] == 503
    finally:
        close_server(server, thread)

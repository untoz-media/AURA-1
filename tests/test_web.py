"""HTTP contract and local-access tests for the AURA application."""

from __future__ import annotations

import http.client
import json
import threading
from types import SimpleNamespace

import pytest

from aura.web.server import AuraWebApp, create_server


class FakeAssistant:
    def __init__(self):
        self.config = SimpleNamespace(model_name="test/model")
        self.settings = SimpleNamespace(active_profile="fast")
        self.persistent_memory = SimpleNamespace(data={"name": "Luis"})

    def list_tools(self):
        return [SimpleNamespace(name="calculator")]


class FakeAgent:
    RUNTIME_VERSION = "1.4"

    def __init__(self, assistant):
        self.assistant = assistant
        self.messages = []
        self.confirmations = []
        self.has_pending_confirmation = False

    def capabilities(self):
        return ["local_chat", "system_state", "state_awareness"]

    def handle_message(self, message):
        self.messages.append(message)
        return {"kind": "message", "response": f"Resposta: {message}", "runtime": "1.4"}

    def confirm(self, token, approved):
        self.confirmations.append((token, approved))
        return {"kind": "cancelled" if not approved else "action_result", "response": "ok"}

    def clear(self):
        self.messages.clear()
        self.has_pending_confirmation = False

    def system_state(self):
        return {
            "sucesso": True,
            "cpu_percent": 21.5,
            "ram": {"percentagem_usada": 47.0},
            "pressao": "normal",
            "bateria": None,
            "foreground_app": "Code.exe",
        }


@pytest.fixture
def web_server():
    app = AuraWebApp(assistant_factory=FakeAssistant, agent_factory=FakeAgent)
    app.load()
    server = create_server(app, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield app, server
    server.shutdown()
    server.server_close()
    thread.join()


def request(server, method, path, payload=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
    body = json.dumps(payload) if payload is not None else None
    request_headers = {"Host": f"127.0.0.1:{server.server_port}"}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    request_headers.update(headers or {})
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    content = response.read()
    connection.close()
    return response.status, dict(response.headers), content


def test_status_and_static_interface(web_server):
    _, server = web_server
    status, headers, body = request(server, "GET", "/api/status")
    assert status == 200
    payload = json.loads(body)
    assert payload["state"] == "ready"
    assert payload["agent_runtime"] == "1.4"
    assert "system_state" in payload["capabilities"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    status, _, body = request(server, "GET", "/")
    assert status == 200
    assert b"AURA-1" in body
    assert b"Runtime v1.4" in body
    assert b"Protected actions" in body
    status, _, body = request(server, "GET", "/agent.css")
    assert status == 200 and b"confirm-card" in body
    status, _, body = request(server, "GET", "/favicon.svg")
    assert status == 200 and b"#00A3FF" in body
    status, _, body = request(server, "GET", "/fonts/Sora-Variable.ttf")
    assert status == 200 and len(body) > 1000


def test_brand_tokens_and_agent_ui_states(web_server):
    _, server = web_server
    _, _, css = request(server, "GET", "/app.css")
    for token in (b"#05070a", b"#1a1e26", b"#f4f7ff", b"#00a3ff", b"#7b61ff"):
        assert token in css.lower()
    _, _, js = request(server, "GET", "/app.js")
    assert b"setCoreState('generating')" in js
    assert b"/api/confirm" in js
    assert b"/api/system-state" in js
    assert b"renderPhases" in js


def test_chat_clear_confirmation_and_system_state(web_server):
    app, server = web_server
    status, _, body = request(server, "POST", "/api/chat", {"message": "Olá"})
    assert status == 200
    assert json.loads(body)["response"] == "Resposta: Olá"
    assert app.agent.messages == ["Olá"]
    status, _, body = request(server, "GET", "/api/system-state")
    assert status == 200
    assert json.loads(body)["cpu_percent"] == 21.5
    status, _, body = request(server, "POST", "/api/confirm", {"token": "token-123", "approved": True})
    assert status == 200
    assert json.loads(body)["response"] == "ok"
    assert app.agent.confirmations == [("token-123", True)]
    assert request(server, "POST", "/api/clear", {})[0] == 200
    assert app.agent.messages == []


@pytest.mark.parametrize("payload", [{}, {"message": ""}, {"message": 12}, {"message": "x" * 4097}])
def test_invalid_chat(web_server, payload):
    _, server = web_server
    assert request(server, "POST", "/api/chat", payload)[0] == 400


@pytest.mark.parametrize("payload", [{}, {"token": ""}, {"token": 42, "approved": True}, {"token": "x", "approved": "yes"}])
def test_invalid_confirmation(web_server, payload):
    _, server = web_server
    assert request(server, "POST", "/api/confirm", payload)[0] == 400


def test_local_host_and_origin_checks(web_server):
    _, server = web_server
    assert request(server, "GET", "/api/status", headers={"Host": "malicious.example"})[0] == 403
    origin = {"Origin": "https://malicious.example"}
    assert request(server, "POST", "/api/clear", {}, origin)[0] == 403


def test_loading_and_busy_states(web_server):
    app, server = web_server
    app.state = "loading"
    assert request(server, "POST", "/api/chat", {"message": "Olá"})[0] == 503
    assert request(server, "GET", "/api/system-state")[0] == 503
    app.state = "ready"
    app.chat_lock.acquire()
    try:
        assert request(server, "POST", "/api/chat", {"message": "Olá"})[0] == 409
    finally:
        app.chat_lock.release()


def test_server_rejects_external_binding():
    with pytest.raises(ValueError):
        create_server(AuraWebApp(), host="0.0.0.0")

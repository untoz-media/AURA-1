"""HTTP contract and local-access tests for the browser interface."""

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
        self.messages = []

    def list_tools(self):
        return [SimpleNamespace(name="calculator")]

    def chat(self, message):
        self.messages.append(message)
        return f"Resposta: {message}"

    def clear_memory(self):
        self.messages.clear()


@pytest.fixture
def web_server():
    app = AuraWebApp(assistant_factory=FakeAssistant)
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
    assert json.loads(body)["state"] == "ready"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    status, _, body = request(server, "GET", "/")
    assert status == 200
    assert b"AURA-1" in body


def test_chat_and_clear(web_server):
    app, server = web_server
    status, _, body = request(server, "POST", "/api/chat", {"message": "Olá"})
    assert status == 200
    assert json.loads(body)["response"] == "Resposta: Olá"
    assert app.assistant.messages == ["Olá"]
    assert request(server, "POST", "/api/clear", {})[0] == 200
    assert app.assistant.messages == []


@pytest.mark.parametrize("payload", [{}, {"message": ""}, {"message": 12}, {"message": "x" * 4097}])
def test_invalid_chat(web_server, payload):
    _, server = web_server
    assert request(server, "POST", "/api/chat", payload)[0] == 400


def test_local_host_and_origin_checks(web_server):
    _, server = web_server
    assert request(server, "GET", "/api/status", headers={"Host": "malicious.example"})[0] == 403
    origin = {"Origin": "https://malicious.example"}
    assert request(server, "POST", "/api/clear", {}, origin)[0] == 403


def test_loading_and_busy_states(web_server):
    app, server = web_server
    app.state = "loading"
    assert request(server, "POST", "/api/chat", {"message": "Olá"})[0] == 503
    app.state = "ready"
    app.chat_lock.acquire()
    try:
        assert request(server, "POST", "/api/chat", {"message": "Olá"})[0] == 409
    finally:
        app.chat_lock.release()


def test_server_rejects_external_binding():
    with pytest.raises(ValueError):
        create_server(AuraWebApp(), host="0.0.0.0")

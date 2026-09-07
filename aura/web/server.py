"""Dependency-free, localhost-only HTTP server for AURA-1."""

from __future__ import annotations

import json
import threading
import webbrowser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

from aura.core.assistant import AuraAssistant
from aura import __version__

STATIC_ROOT = Path(__file__).with_name("static")
MAX_BODY_BYTES = 16 * 1024
MAX_MESSAGE_CHARS = 4096


@dataclass
class AuraWebApp:
    """Own the single local assistant instance and its loading state."""

    assistant_factory: Callable[[], AuraAssistant] = AuraAssistant
    assistant: AuraAssistant | None = None
    state: str = "loading"
    error: str | None = None
    chat_lock: threading.Lock = field(default_factory=threading.Lock)

    def load(self) -> None:
        try:
            self.assistant = self.assistant_factory()
        except Exception:
            self.state = "error"
            self.error = "The local model could not be loaded. Check the terminal for details."
            raise
        else:
            self.state = "ready"

    def public_state(self) -> dict:
        data = {"state": self.state, "error": self.error, "version": __version__}
        if self.assistant is not None:
            data.update({
                "model": self.assistant.config.model_name,
                "profile": self.assistant.settings.active_profile,
                "tools": [tool.name for tool in self.assistant.list_tools()],
                "memory_count": len(self.assistant.persistent_memory.data),
            })
        return data


def _handler(app: AuraWebApp):
    class Handler(BaseHTTPRequestHandler):
        server_version = "AURA-1"

        def log_message(self, format: str, *args) -> None:
            print(f"[web] {self.address_string()} - {format % args}")

        def _security_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
            )

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self._security_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload: dict) -> None:
            self._send(status, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def _trusted_request(self) -> bool:
            host = self.headers.get("Host", "").lower()
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if host not in allowed:
                return False
            origin = self.headers.get("Origin")
            if origin:
                parsed = urlsplit(origin)
                if parsed.scheme != "http" or parsed.netloc.lower() not in allowed:
                    return False
            return True

        def _read_json(self) -> dict | None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return None
            if length <= 0 or length > MAX_BODY_BYTES or self.headers.get_content_type() != "application/json":
                return None
            try:
                value = json.loads(self.rfile.read(length))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None
            return value if isinstance(value, dict) else None

        def do_GET(self) -> None:
            if not self._trusted_request():
                self._json(HTTPStatus.FORBIDDEN, {"error": "Invalid local request."})
                return
            path = urlsplit(self.path).path
            if path == "/api/status":
                self._json(HTTPStatus.OK, app.public_state())
                return
            static = {"/": "index.html", "/app.css": "app.css", "/app.js": "app.js", "/favicon.svg": "favicon.svg", "/fonts/Sora-Variable.ttf": "fonts/Sora-Variable.ttf"}.get(path)
            if static is None:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
                return
            types = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml", ".ttf": "font/ttf"}
            self._send(HTTPStatus.OK, (STATIC_ROOT / static).read_bytes(), types[Path(static).suffix])

        def do_POST(self) -> None:
            if not self._trusted_request():
                self._json(HTTPStatus.FORBIDDEN, {"error": "Invalid local request."})
                return
            payload = self._read_json()
            if payload is None:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid request."})
                return
            path = urlsplit(self.path).path
            if app.state != "ready" or app.assistant is None:
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "AURA is still loading."})
                return
            if path == "/api/chat":
                message = payload.get("message")
                if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE_CHARS:
                    self._json(HTTPStatus.BAD_REQUEST, {"error": "Enter a message between 1 and 4096 characters."})
                    return
                if not app.chat_lock.acquire(blocking=False):
                    self._json(HTTPStatus.CONFLICT, {"error": "AURA is already responding."})
                    return
                try:
                    response = app.assistant.chat(message)
                except Exception as exc:
                    print(f"[web] Falha ao responder: {type(exc).__name__}: {exc}")
                    self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "The response could not be generated."})
                else:
                    self._json(HTTPStatus.OK, {"response": response})
                finally:
                    app.chat_lock.release()
                return
            if path == "/api/clear":
                app.assistant.clear_memory()
                self._json(HTTPStatus.OK, {"ok": True})
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})

    return Handler


def create_server(app: AuraWebApp, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("A interface web só pode ser ligada ao computador local.")
    return ThreadingHTTPServer((host, port), _handler(app))


def run_web_app(port: int = 8765, open_browser: bool = True) -> None:
    app = AuraWebApp()
    server = create_server(app, port=port)
    threading.Thread(target=app.load, name="aura-model-loader", daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"AURA-1 Web: {url}")
    print("Mantém esta janela aberta. Pressiona Ctrl+C para terminar.")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nA encerrar AURA-1 Web…")
    finally:
        server.server_close()

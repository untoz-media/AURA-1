"""Launch AURA-1 as a native desktop window backed by the local app server."""

from __future__ import annotations

import sys
import threading

from aura.web.server import start_app_server


def main() -> None:
    try:
        import webview
    except ImportError as exc:
        raise SystemExit(
            "A interface desktop precisa de pywebview. "
            "Instala requirements-desktop.txt e volta a tentar."
        ) from exc

    _app, server = start_app_server(port=0)
    server_thread = threading.Thread(
        target=server.serve_forever,
        name="aura-local-http",
        daemon=True,
    )
    server_thread.start()

    url = f"http://127.0.0.1:{server.server_port}"
    webview.create_window(
        "AURA-1",
        url,
        width=1280,
        height=820,
        min_size=(900, 620),
        background_color="#05070A",
        text_select=True,
    )

    try:
        webview.start()
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=3)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    main()

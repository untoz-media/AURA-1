"""Launch the AURA-1 local browser interface."""

import argparse
import sys

from aura.web import run_web_app


def main() -> None:
    parser = argparse.ArgumentParser(description="AURA-1 no navegador")
    parser.add_argument("--port", type=int, default=8765, help="Porta local (predefinição: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Não abrir o navegador automaticamente")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("a porta deve estar entre 1 e 65535")
    run_web_app(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    main()

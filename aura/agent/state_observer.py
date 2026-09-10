from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aura.tools.disk_info import DiskInfoTool
from aura.tools.process_manager import ProcessManagerTool


class StateResult(dict):
    """Dict-compatible state result with a human-readable string form."""

    def __init__(self, payload: dict[str, Any], message: str) -> None:
        super().__init__(payload)
        self.message = message

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class PreflightDecision:
    """Read-only decision made immediately before an action executes."""

    skip: bool
    reason: str = ""
    result: dict[str, Any] | None = None


class StateObserver:
    """Observe a narrow, read-only subset of the local computer state.

    Observation can prevent redundant work or describe current state. It cannot
    approve actions, grant permissions, launch/close software or delete data.
    PermissionManager remains authoritative for executable actions.
    """

    MAX_OBSERVED_APPS = 6
    LOW_DISK_GB = 20.0
    DISK_CAUTION_GB = 50.0

    PROCESS_ALIASES = {
        "obs studio": "obs64",
        "obs": "obs64",
        "brave browser": "brave",
        "brave": "brave",
        "google chrome": "chrome",
        "chrome": "chrome",
        "notion": "notion",
        "after effects": "afterfx",
        "adobe after effects": "afterfx",
        "illustrator": "illustrator",
        "adobe illustrator": "illustrator",
        "photoshop": "photoshop",
        "adobe photoshop": "photoshop",
        "premiere pro": "adobe premiere pro",
        "adobe premiere pro": "adobe premiere pro",
        "discord": "discord",
        "spotify": "spotify",
        "bloco de notas": "notepad",
        "notepad": "notepad",
        "paint": "mspaint",
        "vlc": "vlc",
        "capcut": "capcut",
        "firefox": "firefox",
    }

    LOCATION_TARGETS = {
        "downloads",
        "documentos",
        "documents",
        "desktop",
        "area de trabalho",
        "imagens",
        "pictures",
        "videos",
        "musica",
        "music",
    }

    DISK_CONTEXT_HINTS = {
        "live",
        "stream",
        "streaming",
        "gravar",
        "gravacao",
        "editar",
        "edicao",
        "video",
        "render",
        "exportar",
        "exportacao",
        "disco",
        "armazenamento",
        "espaco",
    }

    def __init__(
        self,
        process_manager: ProcessManagerTool | None = None,
        disk_info: DiskInfoTool | None = None,
    ) -> None:
        self.process_manager = process_manager or ProcessManagerTool()
        self.disk_info = disk_info or DiskInfoTool()

    def observe_request(self, request: str) -> str:
        """Return compact read-only facts relevant to one user request."""
        text = self._normalize(request)
        observations: list[str] = []

        for label, process_name in self._mentioned_apps(text):
            state = self.process_manager.is_running(process_name)
            if not state.get("sucesso"):
                continue
            observations.append(
                f"application {label!r}: "
                f"{'running' if state.get('em_execucao') else 'not running'}"
            )

        if any(hint in text for hint in self.DISK_CONTEXT_HINTS):
            disk_path = "C:\\" if os.name == "nt" else str(Path.cwd())
            disk = self.disk_info.run(disk_path)
            if disk.get("sucesso"):
                free_gb = disk.get("livre_gb")
                observations.append(
                    f"disk {disk.get('disco', disk_path)!r}: "
                    f"{free_gb} GB free, {disk.get('percentagem_usada')}% used, "
                    f"{self._disk_health(free_gb)}"
                )

        if not observations:
            return "(no relevant state observed)"
        return "\n".join(f"- {item}" for item in observations)

    def preflight(
        self,
        tool: str,
        action: str,
        arguments: dict[str, Any],
    ) -> PreflightDecision | None:
        """Skip an action only when its desired state is already satisfied."""
        if tool == "app_launcher" and action == "open":
            target = arguments.get("target")
            if not isinstance(target, str) or not target.strip():
                return None

            process_name = self.resolve_process_target(target)
            if process_name is None:
                return None

            state = self.process_manager.is_running(process_name)
            if state.get("sucesso") and state.get("em_execucao"):
                message = f"{target} já estava em execução — não voltei a abrir."
                return PreflightDecision(
                    skip=True,
                    reason=message,
                    result=StateResult(
                        {
                            "sucesso": True,
                            "acao": "estado_satisfeito",
                            "estado": "already_running",
                            "target": target,
                            "processo": process_name,
                        },
                        message,
                    ),
                )
            return None

        if tool == "process_manager" and action == "close":
            target = arguments.get("target")
            if not isinstance(target, str) or not target.strip():
                return None

            process_name = self.resolve_process_target(target) or target.strip()
            state = self.process_manager.is_running(process_name)
            if state.get("sucesso") and not state.get("em_execucao"):
                message = (
                    f"{target} já não estava em execução — "
                    "não havia nada para fechar."
                )
                return PreflightDecision(
                    skip=True,
                    reason=message,
                    result=StateResult(
                        {
                            "sucesso": True,
                            "acao": "estado_satisfeito",
                            "estado": "already_closed",
                            "target": target,
                            "processo": process_name,
                        },
                        message,
                    ),
                )
            return None

        if tool == "file_manager" and action == "create_folder":
            path = arguments.get("path")
            if not isinstance(path, str) or not path.strip():
                return None

            target = Path(path.strip())
            try:
                if target.is_dir():
                    message = f"A pasta {target} já existia — não criei outra."
                    return PreflightDecision(
                        skip=True,
                        reason=message,
                        result=StateResult(
                            {
                                "sucesso": True,
                                "acao": "estado_satisfeito",
                                "estado": "folder_exists",
                                "path": str(target),
                            },
                            message,
                        ),
                    )
            except OSError:
                return None

        return None

    @classmethod
    def resolve_process_target(cls, target: str) -> str | None:
        normalized = cls._normalize(target)
        if not normalized or normalized in cls.LOCATION_TARGETS:
            return None
        if normalized.endswith(".exe"):
            normalized = normalized[:-4]
        if normalized in cls.PROCESS_ALIASES:
            return cls.PROCESS_ALIASES[normalized]

        for alias in sorted(cls.PROCESS_ALIASES, key=len, reverse=True):
            if re.search(
                rf"(?:^|\s){re.escape(alias)}(?:\s|$)",
                normalized,
            ):
                return cls.PROCESS_ALIASES[alias]
        return None

    @classmethod
    def _mentioned_apps(cls, normalized_request: str) -> list[tuple[str, str]]:
        matches: list[tuple[str, str]] = []
        seen_processes: set[str] = set()

        for alias in sorted(cls.PROCESS_ALIASES, key=len, reverse=True):
            if not re.search(rf"\b{re.escape(alias)}\b", normalized_request):
                continue
            process_name = cls.PROCESS_ALIASES[alias]
            if process_name in seen_processes:
                continue

            seen_processes.add(process_name)
            matches.append((alias, process_name))
            if len(matches) >= cls.MAX_OBSERVED_APPS:
                break
        return matches

    @classmethod
    def _disk_health(cls, free_gb: Any) -> str:
        if not isinstance(free_gb, (int, float)) or isinstance(free_gb, bool):
            return "space unknown"
        if free_gb < cls.LOW_DISK_GB:
            return "LOW SPACE"
        if free_gb < cls.DISK_CAUTION_GB:
            return "limited space"
        return "space OK"

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = "".join(
            char
            for char in unicodedata.normalize("NFD", text.strip().lower())
            if unicodedata.category(char) != "Mn"
        )
        normalized = re.sub(r"[^a-z0-9.]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

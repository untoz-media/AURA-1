from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from aura.agent.state_observer import StateObserver
from aura.tools.app_launcher import AppLauncherTool
from aura.tools.disk_info import DiskInfoTool
from aura.tools.file_manager import FileManagerTool
from aura.tools.process_manager import ProcessManagerTool
from aura.tools.system_info import SystemInfoTool


class ToolRouter:
    def __init__(self, state_observer: StateObserver | None = None):
        self.app_launcher = AppLauncherTool()
        self.disk_info = DiskInfoTool()
        self.file_manager = FileManagerTool()
        self.process_manager = ProcessManagerTool()
        self.system_info = SystemInfoTool()
        self.state_observer = state_observer or StateObserver()
        self.system_state = self.state_observer.system_state

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.strip().lower()
        text = "".join(
            char
            for char in unicodedata.normalize("NFD", text)
            if unicodedata.category(char) != "Mn"
        )
        text = re.sub(r"[!?.,;:]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _normalize_process_name(name: str) -> str:
        aliases = {
            "bloco de notas": "notepad",
            "notepad": "notepad",
            "spotify": "spotify",
            "brave": "brave",
            "chrome": "chrome",
            "google chrome": "chrome",
            "discord": "discord",
            "paint": "mspaint",
            "explorador": "explorer",
            "explorador de ficheiros": "explorer",
            "explorer": "explorer",
            "powershell": "powershell",
            "command prompt": "cmd",
            "cmd": "cmd",
            "obs": "obs64",
            "obs studio": "obs64",
        }
        cleaned = ToolRouter._normalize_text(name)
        return aliases.get(cleaned, cleaned)

    @staticmethod
    def _strip_polite_prefix(text: str) -> str:
        prefixes = [
            "aura ",
            "aura podes ",
            "aura pode ",
            "podes ",
            "pode ",
            "consegues ",
            "consegue ",
            "por favor ",
            "faz favor ",
            "quero que ",
            "preciso que ",
            "gostava que ",
        ]

        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    changed = True
        return text

    def _preflight(
        self,
        tool: str,
        action: str,
        arguments: dict,
    ) -> dict | None:
        """Return a satisfied-state result without changing the computer."""
        try:
            decision = self.state_observer.preflight(tool, action, arguments)
        except Exception:
            return None
        if decision is not None and decision.skip:
            return decision.result or {
                "sucesso": True,
                "acao": "estado_satisfeito",
            }
        return None

    def route(self, message: str) -> dict | None:
        raw_text = message.strip()
        normalized = self._normalize_text(raw_text)
        normalized = self._strip_polite_prefix(normalized)

        if not normalized:
            return None

        performance_keywords = [
            "o pc esta lento",
            "o computador esta lento",
            "porque e que o pc esta lento",
            "porque e que o computador esta lento",
            "porque esta lento",
            "estado do pc",
            "estado do computador",
            "desempenho do pc",
            "desempenho do computador",
            "performance do pc",
            "uso de cpu",
            "utilizacao de cpu",
            "quanto cpu estou a usar",
            "uso de ram",
            "utilizacao de ram",
            "quanto ram estou a usar",
            "memoria usada",
            "estado da bateria",
            "quanto tenho de bateria",
            "nivel da bateria",
        ]

        if any(keyword in normalized for keyword in performance_keywords):
            return {
                "tool": "system_state",
                "action": "snapshot",
                "result": self.system_state.snapshot(),
            }

        process_list_keywords = [
            "programas abertos",
            "aplicacoes abertas",
            "processos abertos",
            "processos a correr",
            "processos em execucao",
            "o que esta aberto",
            "o que tenho aberto",
            "que programas estao abertos",
            "que aplicacoes estao abertas",
            "lista os processos",
            "mostra os processos",
        ]

        ram_keywords = [
            "mais memoria",
            "mais ram",
            "gastar mais memoria",
            "gasta mais memoria",
            "gastar mais ram",
            "gasta mais ram",
            "usar mais memoria",
            "usa mais memoria",
            "usar mais ram",
            "usa mais ram",
            "consumir mais memoria",
            "consome mais memoria",
        ]

        if any(keyword in normalized for keyword in process_list_keywords):
            return {
                "tool": "process_manager",
                "action": "list",
                "result": self.process_manager.list_processes(10),
            }

        if any(keyword in normalized for keyword in ram_keywords):
            return {
                "tool": "process_manager",
                "action": "list",
                "result": self.process_manager.list_processes(10),
            }

        running_patterns = [
            r"^(?:o |a )?(.+?) esta aberto$",
            r"^(?:o |a )?(.+?) esta aberta$",
            r"^(?:o |a )?(.+?) esta a correr$",
            r"^(?:o |a )?(.+?) esta em execucao$",
            r"^tenho (?:o |a )?(.+?) aberto$",
            r"^tenho (?:o |a )?(.+?) aberta$",
            r"^(.+?) esta aberto no computador$",
            r"^(.+?) esta aberto no pc$",
        ]

        for pattern in running_patterns:
            match = re.match(pattern, normalized)
            if match:
                target = self._normalize_process_name(match.group(1).strip())
                return {
                    "tool": "process_manager",
                    "action": "is_running",
                    "target": target,
                    "result": self.process_manager.is_running(target),
                }

        close_patterns = [
            r"^(?:fecha|fechar) (?:o |a )?(.+)$",
            r"^(?:encerra|encerrar) (?:o |a )?(.+)$",
            r"^(?:termina|terminar) (?:o |a )?(.+)$",
            r"^(?:desliga|desligar) (?:o |a )?(.+)$",
        ]

        for pattern in close_patterns:
            match = re.match(pattern, normalized)
            if match:
                target = self._normalize_process_name(match.group(1).strip())
                state_result = self._preflight(
                    "process_manager",
                    "close",
                    {"target": target},
                )
                if state_result is not None:
                    return {
                        "tool": "process_manager",
                        "action": "close",
                        "target": target,
                        "result": state_result,
                    }
                return {
                    "tool": "process_manager",
                    "action": "close_request",
                    "target": target,
                    "requires_confirmation": True,
                }

        open_patterns = [
            r"^(?:abre|abrir) (?:o |a |os |as )?(.+)$",
            r"^quero abrir (?:o |a )?(.+)$",
            r"^quero que abras (?:o |a )?(.+)$",
            r"^inicia (?:o |a )?(.+)$",
            r"^iniciar (?:o |a )?(.+)$",
            r"^lanca (?:o |a )?(.+)$",
            r"^lancar (?:o |a )?(.+)$",
        ]

        for pattern in open_patterns:
            match = re.match(pattern, normalized)
            if match:
                target = match.group(1).strip()
                state_result = self._preflight(
                    "app_launcher",
                    "open",
                    {"target": target},
                )
                if state_result is not None:
                    return {
                        "tool": "app_launcher",
                        "action": "open",
                        "target": target,
                        "result": state_result,
                    }
                return {
                    "tool": "app_launcher",
                    "action": "open",
                    "target": target,
                    "result": self.app_launcher.run(target),
                }

        disk_keywords = [
            "quanto espaco tenho",
            "espaco livre",
            "espaco no disco",
            "armazenamento livre",
            "quanto armazenamento tenho",
            "quanto tenho de armazenamento",
            "quanto disco tenho",
        ]

        if any(keyword in normalized for keyword in disk_keywords):
            return {
                "tool": "disk_info",
                "action": "info",
                "result": self.disk_info.run(),
            }

        system_keywords = [
            "que sistema operativo",
            "qual sistema operativo",
            "informacoes do sistema",
            "informacao do pc",
            "informacoes do pc",
            "quantos nucleos",
            "quantos processadores logicos",
            "qual e o meu cpu",
            "que cpu tenho",
        ]

        if any(keyword in normalized for keyword in system_keywords):
            return {
                "tool": "system_info",
                "action": "info",
                "result": self.system_info.run(),
            }

        folder_patterns = [
            r"^(?:cria|criar) uma pasta chamada (.+)$",
            r"^(?:cria|criar) uma pasta com o nome (.+)$",
            r"^(?:cria|criar) pasta chamada (.+)$",
            r"^(?:cria|criar) pasta (.+)$",
        ]

        for pattern in folder_patterns:
            match = re.match(pattern, normalized)
            if match:
                folder_name = match.group(1).strip().strip("\"'")
                target = Path.home() / "Desktop" / folder_name
                state_result = self._preflight(
                    "file_manager",
                    "create_folder",
                    {"path": str(target)},
                )
                return {
                    "tool": "file_manager",
                    "action": "create_folder",
                    "target": str(target),
                    "result": (
                        state_result
                        if state_result is not None
                        else self.file_manager.create_folder(str(target))
                    ),
                }

        desktop_folder_patterns = [
            r"^cria uma pasta no ambiente de trabalho chamada (.+)$",
            r"^cria uma pasta no desktop chamada (.+)$",
            r"^cria no desktop uma pasta chamada (.+)$",
            r"^cria no ambiente de trabalho uma pasta chamada (.+)$",
        ]

        for pattern in desktop_folder_patterns:
            match = re.match(pattern, normalized)
            if match:
                folder_name = match.group(1).strip().strip("\"'")
                target = Path.home() / "Desktop" / folder_name
                state_result = self._preflight(
                    "file_manager",
                    "create_folder",
                    {"path": str(target)},
                )
                return {
                    "tool": "file_manager",
                    "action": "create_folder",
                    "target": str(target),
                    "result": (
                        state_result
                        if state_result is not None
                        else self.file_manager.create_folder(str(target))
                    ),
                }

        return None

    def execute_confirmed_action(
        self,
        tool: str,
        action: str,
        target: str,
    ) -> dict:
        if tool == "process_manager" and action == "close":
            state_result = self._preflight(
                "process_manager",
                "close",
                {"target": target},
            )
            if state_result is not None:
                return state_result
            return self.process_manager.close(target)

        return {
            "sucesso": False,
            "erro": "Ação confirmada desconhecida.",
        }

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from aura.tools.app_discovery import AppDiscoveryTool


class AppLauncherTool:
    name = "app_launcher"
    description = (
        "Abre aplicações, localizações conhecidas "
        "e aplicações descobertas no Windows."
    )

    APPS = {
        "spotify": "spotify:",
        "notepad": "notepad.exe",
        "bloco de notas": "notepad.exe",
        "calculadora": "calc.exe",
        "calculator": "calc.exe",
        "explorador": "explorer.exe",
        "explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
    }

    LOCATIONS = {
        "downloads": Path.home() / "Downloads",
        "documentos": Path.home() / "Documents",
        "documents": Path.home() / "Documents",
        "desktop": Path.home() / "Desktop",
        "área de trabalho": Path.home() / "Desktop",
        "imagens": Path.home() / "Pictures",
        "pictures": Path.home() / "Pictures",
        "videos": Path.home() / "Videos",
        "vídeos": Path.home() / "Videos",
        "musica": Path.home() / "Music",
        "música": Path.home() / "Music",
    }

    def __init__(self):
        self.app_discovery = AppDiscoveryTool()

    def run(self, target: str) -> dict:
        target_clean = target.strip().lower()

        if not target_clean:
            return {
                "sucesso": False,
                "erro": "Não foi indicada nenhuma aplicação ou localização.",
            }

        try:
            # ----------------------------------------------
            # KNOWN LOCATIONS
            # ----------------------------------------------

            if target_clean in self.LOCATIONS:
                path = self.LOCATIONS[target_clean]

                if not path.exists():
                    return {
                        "sucesso": False,
                        "erro": f"A localização não existe: {path}",
                    }

                os.startfile(path)

                return {
                    "sucesso": True,
                    "acao": "abrir_pasta",
                    "target": str(path),
                    "origem": "location",
                }

            # ----------------------------------------------
            # BUILT-IN APPS
            # ----------------------------------------------

            if target_clean in self.APPS:
                command = self.APPS[target_clean]

                if command.endswith(":"):
                    os.startfile(command)

                else:
                    subprocess.Popen(
                        [command],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )

                return {
                    "sucesso": True,
                    "acao": "abrir_app",
                    "target": target_clean,
                    "origem": "builtin",
                }

            # ----------------------------------------------
            # AUTOMATIC APP DISCOVERY
            # ----------------------------------------------

            discovered = self.app_discovery.open(target)

            if discovered.get("sucesso"):
                return {
                    "sucesso": True,
                    "acao": "abrir_app_descoberta",
                    "target": target_clean,
                    "nome": discovered.get("nome", target),
                    "caminho": discovered.get("caminho"),
                    "origem": "discovery",
                }

            return {
                "sucesso": False,
                "erro": discovered.get(
                    "erro",
                    f"Não encontrei a aplicação '{target}'.",
                ),
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }
from __future__ import annotations

import os
import subprocess
from pathlib import Path


class AppDiscoveryTool:
    name = "app_discovery"
    description = (
        "Descobre, pesquisa e abre aplicações instaladas no Windows."
    )

    # Atalhos que normalmente NÃO representam a aplicação principal.
    LOW_PRIORITY_KEYWORDS = {
        "settings",
        "setting",
        "properties",
        "property",
        "preferences",
        "configuration",
        "configure",
        "config",
        "uninstall",
        "uninstaller",
        "remove",
        "help",
        "documentation",
        "manual",
        "readme",
        "license",
        "licence",
        "troubleshoot",
        "repair",
        "update",
        "updater",
        "website",
        "homepage",
        "safe mode",
        "propriedades",
        "definições",
        "definicoes",
        "configuração",
        "configuracao",
        "desinstalar",
        "ajuda",
    }

    def __init__(self):
        self.search_paths = self._default_search_paths()

    # --------------------------------------------------
    # SEARCH LOCATIONS
    # --------------------------------------------------

    def _default_search_paths(self) -> list[Path]:
        paths: list[Path] = []

        appdata = os.getenv("APPDATA")
        programdata = os.getenv("PROGRAMDATA")

        if appdata:
            paths.append(
                Path(appdata)
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
            )

        if programdata:
            paths.append(
                Path(programdata)
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
            )

        user_desktop = Path.home() / "Desktop"

        if user_desktop.exists():
            paths.append(user_desktop)

        public_desktop = Path(
            "C:/Users/Public/Desktop"
        )

        if public_desktop.exists():
            paths.append(public_desktop)

        return paths

    # --------------------------------------------------
    # NORMALIZATION
    # --------------------------------------------------

    @staticmethod
    def _clean_name(name: str) -> str:
        cleaned = (
            name.lower()
            .replace("-", " ")
            .replace("_", " ")
            .replace(".", " ")
            .replace("(", " ")
            .replace(")", " ")
        )

        return " ".join(
            cleaned.split()
        )

    # --------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------

    def discover(self) -> dict:
        apps: dict[str, dict] = {}

        try:
            for base_path in self.search_paths:

                if not base_path.exists():
                    continue

                for item in base_path.rglob("*"):

                    if not item.is_file():
                        continue

                    suffix = item.suffix.lower()

                    if suffix not in {
                        ".lnk",
                        ".url",
                        ".exe",
                    }:
                        continue

                    name = item.stem.strip()

                    if not name:
                        continue

                    key = (
                        self._clean_name(name)
                        + "|"
                        + str(item).lower()
                    )

                    apps[key] = {
                        "nome": name,
                        "caminho": str(item),
                        "tipo": suffix,
                    }

            discovered = sorted(
                apps.values(),
                key=lambda app: (
                    app["nome"].lower()
                ),
            )

            return {
                "sucesso": True,
                "total": len(discovered),
                "apps": discovered,
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }

    # --------------------------------------------------
    # MATCH SCORING
    # --------------------------------------------------

    def _score_match(
        self,
        query: str,
        app_name: str,
    ) -> int:

        query_clean = self._clean_name(query)
        app_clean = self._clean_name(app_name)

        if not query_clean or not app_clean:
            return 0

        score = 0

        # Match perfeito.
        if app_clean == query_clean:
            score += 1000

        # Exemplo:
        # OBS -> OBS Studio
        elif app_clean.startswith(
            query_clean + " "
        ):
            score += 850

        # Exemplo:
        # After Effects -> Adobe After Effects 2026
        elif query_clean in app_clean:
            score += 650

        elif app_clean in query_clean:
            score += 500

        else:
            query_words = set(
                query_clean.split()
            )

            app_words = set(
                app_clean.split()
            )

            common_words = (
                query_words
                & app_words
            )

            score += (
                len(common_words)
                * 100
            )

        # Penalizar atalhos que normalmente
        # não são a app principal.
        for keyword in self.LOW_PRIORITY_KEYWORDS:

            if keyword in app_clean:
                score -= 700

        # Nomes demasiado longos tendem
        # a ser ferramentas auxiliares.
        extra_length = max(
            0,
            len(app_clean)
            - len(query_clean),
        )

        score -= min(
            extra_length,
            100,
        )

        return score

    # --------------------------------------------------
    # FIND
    # --------------------------------------------------

    def find(
        self,
        query: str,
    ) -> dict:

        result = self.discover()

        if not result.get("sucesso"):
            return result

        apps = result.get(
            "apps",
            [],
        )

        scored_matches = []

        for app in apps:

            score = self._score_match(
                query,
                app.get(
                    "nome",
                    "",
                ),
            )

            if score <= 0:
                continue

            candidate = dict(app)
            candidate["score"] = score

            scored_matches.append(
                candidate
            )

        scored_matches.sort(
            key=lambda app: (
                -app["score"],
                len(app["nome"]),
                app["nome"].lower(),
            )
        )

        if not scored_matches:
            return {
                "sucesso": True,
                "encontrado": False,
                "query": query,
                "matches": [],
            }

        return {
            "sucesso": True,
            "encontrado": True,
            "query": query,
            "matches": scored_matches[:10],
        }

    # --------------------------------------------------
    # DETACHED WINDOWS LAUNCH
    # --------------------------------------------------

    @staticmethod
    def _start_detached(
        path: Path,
    ) -> None:
        """
        Abre uma aplicação sem ligar stdout/stderr
        à consola principal do AURA.
        """

        suffix = path.suffix.lower()

        if suffix == ".exe":

            creation_flags = 0

            if os.name == "nt":
                creation_flags = (
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.CREATE_NO_WINDOW
                )

            subprocess.Popen(
                [str(path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )

            return

        # Para .lnk e .url usamos Start-Process.
        #
        # Isto permite ao Windows resolver corretamente
        # o atalho sem manter a app ligada à consola AURA.

        escaped_path = str(path).replace(
            "'",
            "''",
        )

        command = (
            "Start-Process "
            f"-FilePath '{escaped_path}'"
        )

        creation_flags = 0

        if os.name == "nt":
            creation_flags = (
                subprocess.CREATE_NO_WINDOW
            )

        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-WindowStyle",
                "Hidden",
                "-Command",
                command,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )

    # --------------------------------------------------
    # OPEN
    # --------------------------------------------------

    def open(
        self,
        query: str,
    ) -> dict:

        result = self.find(
            query
        )

        if not result.get(
            "sucesso"
        ):
            return result

        if not result.get(
            "encontrado"
        ):
            return {
                "sucesso": False,
                "erro": (
                    "Não encontrei nenhuma aplicação "
                    f"correspondente a '{query}'."
                ),
            }

        matches = result.get(
            "matches",
            [],
        )

        if not matches:
            return {
                "sucesso": False,
                "erro": (
                    "Nenhuma aplicação encontrada."
                ),
            }

        app = matches[0]

        path = Path(
            app["caminho"]
        )

        try:
            self._start_detached(
                path
            )

            return {
                "sucesso": True,
                "acao": "abrir_app_descoberta",
                "nome": app["nome"],
                "caminho": app["caminho"],
                "score": app.get(
                    "score"
                ),
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }
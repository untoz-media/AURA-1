from __future__ import annotations

import psutil


class ProcessManagerTool:
    name = "process_manager"
    description = "Consulta e gere aplicações em execução no computador."

    # Processos que o AURA nunca deverá terminar.
    PROTECTED_PROCESSES = {
        "system",
        "registry",
        "memory compression",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "winlogon.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "dwm.exe",
        "explorer.exe",
    }

    def list_processes(self, limit: int = 20) -> dict:
        """Lista processos ordenados por utilização de memória."""

        processes = []

        try:
            for process in psutil.process_iter(
                ["pid", "name", "memory_info"]
            ):
                try:
                    info = process.info

                    name = info.get("name") or "Desconhecido"
                    memory_info = info.get("memory_info")

                    memory_mb = (
                        memory_info.rss / (1024 ** 2)
                        if memory_info
                        else 0
                    )

                    processes.append(
                        {
                            "pid": info["pid"],
                            "nome": name,
                            "memoria_mb": round(memory_mb, 1),
                        }
                    )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                ):
                    continue

            processes.sort(
                key=lambda item: item["memoria_mb"],
                reverse=True,
            )

            return {
                "sucesso": True,
                "total": len(processes),
                "processos": processes[:limit],
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }

    def is_running(self, name: str) -> dict:
        """Verifica se uma aplicação/processo está em execução."""

        target = name.lower().strip()

        matches = []

        try:
            for process in psutil.process_iter(
                ["pid", "name"]
            ):
                try:
                    process_name = (
                        process.info.get("name") or ""
                    )

                    clean_name = process_name.lower()

                    if (
                        target == clean_name
                        or target == clean_name.removesuffix(".exe")
                    ):
                        matches.append(
                            {
                                "pid": process.info["pid"],
                                "nome": process_name,
                            }
                        )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                ):
                    continue

            return {
                "sucesso": True,
                "em_execucao": bool(matches),
                "processos": matches,
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }

    def close(self, name: str) -> dict:
        """Fecha processos pelo nome, exceto processos protegidos."""

        target = name.lower().strip()

        if not target.endswith(".exe"):
            target_exe = f"{target}.exe"
        else:
            target_exe = target

        if (
            target in self.PROTECTED_PROCESSES
            or target_exe in self.PROTECTED_PROCESSES
        ):
            return {
                "sucesso": False,
                "erro": (
                    f"O processo '{name}' está protegido "
                    "e não pode ser terminado pelo AURA."
                ),
            }

        closed = []

        try:
            for process in psutil.process_iter(
                ["pid", "name"]
            ):
                try:
                    process_name = (
                        process.info.get("name") or ""
                    )

                    clean_name = process_name.lower()

                    if (
                        target == clean_name
                        or target_exe == clean_name
                        or target == clean_name.removesuffix(".exe")
                    ):
                        process.terminate()

                        closed.append(
                            {
                                "pid": process.info["pid"],
                                "nome": process_name,
                            }
                        )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                ):
                    continue

            if not closed:
                return {
                    "sucesso": False,
                    "erro": (
                        f"Não encontrei nenhum processo "
                        f"chamado '{name}'."
                    ),
                }

            return {
                "sucesso": True,
                "acao": "fechar_processo",
                "processos": closed,
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }
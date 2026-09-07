"""Safe local system information tool for AURA-1."""

from __future__ import annotations

import os
import platform

from aura.tools.base import Tool


class SystemInfoTool(Tool):
    """Expose a small allowlist of read-only local system facts."""

    def __init__(self) -> None:
        super().__init__(
            name="system_info",
            description="Obtém informação básica e segura sobre o sistema local.",
        )

    def run(self, **kwargs) -> dict[str, str | int]:
        """Return read-only system facts without executing shell commands."""
        if kwargs:
            raise ValueError("A tool system_info não aceita argumentos.")

        memory_gb = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024**3), 2) if hasattr(os, "sysconf") else "desconhecida"

        return {
            "sistema_operativo": platform.system() or "desconhecido",
            "versao_sistema": platform.release() or "desconhecida",
            "arquitetura": platform.machine() or "desconhecida",
            "processador": platform.processor() or platform.machine() or "desconhecido",
            "python": platform.python_version(),
            "cpu_logical": os.cpu_count() or 0,
            "ram_gb": memory_gb,
        }

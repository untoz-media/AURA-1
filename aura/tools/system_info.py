"""Safe local system information tool for AURA-1."""

from __future__ import annotations

import ctypes
import os
import platform

from aura.tools.base import Tool


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _ram_gb() -> tuple[float | None, float | None]:
    """Return total and available physical RAM in GiB without shell calls."""
    if os.name == "nt":
        status = _MemoryStatusEx()
        status.dwLength = ctypes.sizeof(_MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return round(status.ullTotalPhys / (1024**3), 2), round(status.ullAvailPhys / (1024**3), 2)
        return None, None

    if hasattr(os, "sysconf"):
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
            total = page_size * os.sysconf("SC_PHYS_PAGES") / (1024**3)
            available = page_size * os.sysconf("SC_AVPHYS_PAGES") / (1024**3)
            return round(total, 2), round(available, 2)
        except (OSError, ValueError):
            pass

    return None, None


class SystemInfoTool(Tool):
    """Expose a small allowlist of read-only local system facts."""

    def __init__(self) -> None:
        super().__init__(
            name="system_info",
            description="Obtém informação básica e segura sobre o sistema local.",
        )

    def run(self, **kwargs) -> dict[str, str | int | float | None]:
        """Return read-only system facts without executing shell commands."""
        if kwargs:
            raise ValueError("A tool system_info não aceita argumentos.")

        total_ram, available_ram = _ram_gb()
        return {
            "sistema_operativo": platform.system() or "desconhecido",
            "versao_sistema": platform.release() or "desconhecida",
            "arquitetura": platform.machine() or "desconhecida",
            "processador": platform.processor() or platform.machine() or "desconhecido",
            "python": platform.python_version(),
            "cpu_logical": os.cpu_count() or 0,
            "ram_total_gb": total_ram,
            "ram_disponivel_gb": available_ram,
        }

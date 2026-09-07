"""Safe local system information tool for AURA-1."""

from __future__ import annotations

import ctypes
import os
import platform

from aura.tools.base import Tool


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint32),
        ("load", ctypes.c_uint32),
        ("total_phys", ctypes.c_uint64),
        ("avail_phys", ctypes.c_uint64),
        ("total_page", ctypes.c_uint64),
        ("avail_page", ctypes.c_uint64),
        ("total_virtual", ctypes.c_uint64),
        ("avail_virtual", ctypes.c_uint64),
        ("avail_extended", ctypes.c_uint64),
    ]


def _memory_gb() -> tuple[float | str, float | str]:
    """Read physical RAM; unavailable platform counters remain unknown."""
    total = available = "desconhecida"
    try:
        if platform.system() == "Windows":
            status = _MemoryStatus()
            status.length = ctypes.sizeof(status)
            query = ctypes.WinDLL("kernel32", use_last_error=True).GlobalMemoryStatusEx
            query.argtypes = [ctypes.POINTER(_MemoryStatus)]
            query.restype = ctypes.c_int
            if not query(ctypes.byref(status)):
                return total, available
            return round(status.total_phys / 1024**3, 2), round(status.avail_phys / 1024**3, 2)
        if hasattr(os, "sysconf"):
            page = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")
            if page > 0 and pages > 0:
                total = round(page * pages / 1024**3, 2)
            free_pages = os.sysconf("SC_AVPHYS_PAGES")
            if page > 0 and free_pages >= 0:
                available = round(page * free_pages / 1024**3, 2)
    except (AttributeError, OSError, ValueError):
        pass
    return total, available


class SystemInfoTool(Tool):
    """Expose a small allowlist of read-only local system facts."""

    def __init__(self) -> None:
        super().__init__(
            name="system_info",
            description="Returns basic, read-only information about the local system.",
        )

    def run(self, **kwargs) -> dict[str, str | int | float]:
        """Return read-only system facts without executing shell commands."""
        if kwargs:
            raise ValueError("A tool system_info não aceita argumentos.")

        memory_gb, available_gb = _memory_gb()
        return {
            "sistema_operativo": platform.system() or "desconhecido",
            "versao_sistema": platform.release() or "desconhecida",
            "arquitetura": platform.machine() or "desconhecida",
            "processador": platform.processor() or platform.machine() or "desconhecido",
            "python": platform.python_version(),
            "cpu_logical": os.cpu_count() or 0,
            "ram_gb": memory_gb,
            "ram_total_gb": memory_gb,
            "ram_disponivel_gb": available_gb,
        }

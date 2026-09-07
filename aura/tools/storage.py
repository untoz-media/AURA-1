"""Read-only storage analysis tool for AURA-1."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from aura.tools.base import Tool


class StorageAnalyzerTool(Tool):
    """Analyze local storage without modifying files."""

    def __init__(self) -> None:
        super().__init__(
            name="storage_analyzer",
            description=(
                "Returns read-only disk usage and the largest folders in the current user's home directory."
            ),
        )

    @staticmethod
    def _folder_size(path: Path) -> int:
        total = 0
        try:
            for root, dirs, files in os.walk(path, topdown=True, onerror=lambda _exc: None):
                # Avoid traversing directory symlinks/junction-like links where Python exposes them as symlinks.
                dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
                for name in files:
                    file_path = Path(root) / name
                    try:
                        if not file_path.is_symlink():
                            total += file_path.stat().st_size
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            return total
        return total

    @staticmethod
    def _gb(value: int) -> float:
        return round(value / 1024**3, 2)

    def run(self, **kwargs) -> dict:
        """Return disk totals and largest first-level folders under the user's home directory."""
        allowed = {"top_n"}
        unexpected = set(kwargs) - allowed
        if unexpected:
            raise ValueError(f"Argumentos não suportados: {', '.join(sorted(unexpected))}")

        top_n = kwargs.get("top_n", 8)
        if isinstance(top_n, str):
            if not top_n.isdigit():
                raise ValueError("top_n deve ser um número inteiro entre 1 e 20.")
            top_n = int(top_n)
        if not isinstance(top_n, int) or not 1 <= top_n <= 20:
            raise ValueError("top_n deve ser um número inteiro entre 1 e 20.")

        home = Path.home()
        usage = shutil.disk_usage(home)

        folders: list[dict[str, str | float]] = []
        try:
            children = list(home.iterdir())
        except (OSError, PermissionError):
            children = []

        for child in children:
            try:
                if child.is_dir() and not child.is_symlink():
                    size = self._folder_size(child)
                    folders.append({
                        "name": child.name,
                        "path": str(child),
                        "size_gb": self._gb(size),
                    })
            except (OSError, PermissionError):
                continue

        folders.sort(key=lambda item: float(item["size_gb"]), reverse=True)

        return {
            "home": str(home),
            "drive_total_gb": self._gb(usage.total),
            "drive_used_gb": self._gb(usage.used),
            "drive_free_gb": self._gb(usage.free),
            "largest_home_folders": folders[:top_n],
            "read_only": True,
            "note": "This tool only inspects storage. It never deletes or modifies files.",
        }

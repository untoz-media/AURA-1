from __future__ import annotations

import shutil
from pathlib import Path


class DiskInfoTool:
    name = "disk_info"
    description = "Obtém informação sobre o espaço disponível num disco."

    def run(self, path: str = "C:\\") -> dict:
        target = Path(path)

        try:
            total, used, free = shutil.disk_usage(target)

            gb = 1024 ** 3

            return {
                "sucesso": True,
                "disco": str(target),
                "total_gb": round(total / gb, 2),
                "usado_gb": round(used / gb, 2),
                "livre_gb": round(free / gb, 2),
                "percentagem_usada": round((used / total) * 100, 1),
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }
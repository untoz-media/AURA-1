from __future__ import annotations

from pathlib import Path


class FileManagerTool:
    name = "file_manager"
    description = "Executa operações seguras em ficheiros e pastas."

    def create_folder(self, path: str) -> dict:
        target = Path(path).expanduser()

        try:
            target.mkdir(parents=True, exist_ok=True)

            return {
                "sucesso": True,
                "acao": "criar_pasta",
                "path": str(target),
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }

    def list_folder(self, path: str) -> dict:
        target = Path(path).expanduser()

        try:
            if not target.exists():
                return {
                    "sucesso": False,
                    "erro": f"A pasta não existe: {target}",
                }

            if not target.is_dir():
                return {
                    "sucesso": False,
                    "erro": f"Não é uma pasta: {target}",
                }

            items = []

            for item in target.iterdir():
                items.append({
                    "nome": item.name,
                    "tipo": "pasta" if item.is_dir() else "ficheiro",
                })

            return {
                "sucesso": True,
                "path": str(target),
                "total": len(items),
                "items": items,
            }

        except Exception as exc:
            return {
                "sucesso": False,
                "erro": str(exc),
            }
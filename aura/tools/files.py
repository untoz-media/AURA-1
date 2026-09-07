"""Read-only, project-scoped file discovery."""

from pathlib import Path, PureWindowsPath
from itertools import islice
import os

from aura.tools.base import Tool


class FileTool(Tool):
    """List names and check existence without reading file contents."""

    def __init__(self, root: str | Path | None = None):
        super().__init__("files", "Lists files and checks their existence inside the project.")
        object.__setattr__(self, "root", Path(root or Path(__file__).resolve().parents[2]).resolve())

    def _path(self, value: str) -> Path:
        if not isinstance(value, str) or not value.strip() or len(value) > 1024:
            raise ValueError("Indica um caminho relativo ao projeto.")
        windows = PureWindowsPath(value)
        if windows.drive or windows.root or any(c in value for c in ':*?<>|"') or any(ord(c) < 32 for c in value):
            raise ValueError("Usa apenas caminhos relativos ao projeto, sem caracteres especiais.")
        parts = Path(value.replace('\\', '/')).parts
        if hasattr(os.path, "isreserved") and any(os.path.isreserved(part) for part in parts):
            raise ValueError("Nomes reservados do sistema não são permitidos.")
        if any(part == '..' or part.startswith('.') or part.endswith((' ', '.')) for part in parts):
            raise ValueError("Caminhos superiores e ocultos não são permitidos.")
        candidate = self.root
        for part in parts:
            candidate = candidate / part
            if candidate.is_symlink() or candidate.is_junction():
                raise ValueError("Ligações a outras pastas ou ficheiros não são permitidas.")
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError("O caminho está fora da pasta do projeto.")
        return resolved

    def run(self, action: str = "list", path: str = ".", **kwargs) -> dict:
        if kwargs or action not in ("list", "exists"):
            raise ValueError("Usa a ação list ou exists, com um caminho relativo.")
        target = self._path(path)
        relative = target.relative_to(self.root).as_posix()
        try:
            if action == "exists":
                return {"path": relative, "exists": target.exists(), "is_file": target.is_file(), "is_directory": target.is_dir()}
            if not target.is_dir():
                raise ValueError("A pasta indicada não existe ou não é uma pasta.")
            # Bound traversal as well as model context, including hidden entries.
            with os.scandir(target) as scan:
                entries = list(islice(scan, 101))
            result = []
            for entry in entries[:100]:
                if entry.name.startswith('.'):
                    continue
                child = target / entry.name
                if child.is_symlink() or child.is_junction():
                    continue
                result.append({"name": entry.name, "type": "directory" if child.is_dir() else "file"})
            return {"path": relative, "entries": sorted(result, key=lambda item: item['name'].casefold()), "truncated": len(entries) > 100}
        except OSError:
            raise ValueError("Não foi possível consultar o caminho indicado.") from None

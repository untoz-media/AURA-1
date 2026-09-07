"""Build a source-only AURA-1 Alpha package without local user data."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aura import __version__  # noqa: E402

PACKAGE_ROOT = f"AURA-1-{__version__}"
TOP_LEVEL = (
    "aura.py", "aura_web.py", "iniciar_aura_web.bat", "instalar_aura_windows.bat",
    "requirements-runtime.txt", "README.md", "MODEL_CARD.md", "LICENSE", "NOTICE",
)
DIRECTORIES = ("aura", "docs")


def included_files():
    for name in TOP_LEVEL:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(path)
        yield path
    for directory in DIRECTORIES:
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                yield path


def main() -> None:
    output_dir = ROOT / "dist"
    output_dir.mkdir(exist_ok=True)
    destination = output_dir / f"{PACKAGE_ROOT}-windows.zip"
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in included_files():
            relative = path.relative_to(ROOT)
            archive.write(path, Path(PACKAGE_ROOT) / relative)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(destination.suffix + ".sha256").write_text(
        f"{digest}  {destination.name}\n", encoding="ascii"
    )
    print(destination)


if __name__ == "__main__":
    main()

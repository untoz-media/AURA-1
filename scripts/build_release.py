"""Build a source AURA-1 package without local user data or model weights."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aura import __version__  # noqa: E402

PACKAGE_ROOT = f"AURA-1-{__version__}"
TOP_LEVEL = (
    "aura.py",
    "aura_web.py",
    "aura_desktop.py",
    "iniciar_aura.bat",
    "iniciar_aura_web.bat",
    "instalar_aura_windows.bat",
    "requirements-runtime.txt",
    "requirements-desktop.txt",
    "README.md",
    "MODEL_CARD.md",
    "LICENSE",
    "NOTICE",
    "RELEASE_NOTES.md",
)
DIRECTORIES = ("aura", "docs", "scripts")


def included_files():
    for name in TOP_LEVEL:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(path)
        yield path
    for directory in DIRECTORIES:
        for path in sorted((ROOT / directory).rglob("*")):
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix not in {".pyc", ".pyo"}
            ):
                yield path


def write_checksum(destination: Path) -> Path:
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    checksum = destination.with_suffix(destination.suffix + ".sha256")
    checksum.write_text(f"{digest}  {destination.name}\n", encoding="ascii")
    return checksum


def main() -> None:
    output_dir = ROOT / "dist"
    output_dir.mkdir(exist_ok=True)
    destination = output_dir / f"{PACKAGE_ROOT}-windows-source.zip"
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in included_files():
            relative = path.relative_to(ROOT)
            archive.write(path, Path(PACKAGE_ROOT) / relative)
    write_checksum(destination)
    print(destination)


if __name__ == "__main__":
    main()

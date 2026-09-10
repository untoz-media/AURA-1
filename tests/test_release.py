"""Release metadata and source-package privacy checks."""

from pathlib import Path
from zipfile import ZipFile

from aura import __version__
from scripts import build_release


def test_alpha_version():
    assert __version__ == "0.2.0-alpha.1"


def test_release_allowlist_includes_desktop_app_and_excludes_private_data():
    paths = [path.as_posix() for path in build_release.included_files()]

    required = (
        "NOTICE",
        "RELEASE_NOTES.md",
        "aura.py",
        "aura_web.py",
        "aura_desktop.py",
        "iniciar_aura.bat",
        "requirements-runtime.txt",
        "requirements-desktop.txt",
        "aura/web/agent.py",
        "aura/web/server.py",
        "aura/web/static/index.html",
        "aura/web/static/app.js",
        "aura/web/static/agent.css",
        "scripts/build_desktop.ps1",
        "docs/desktop-app.md",
    )
    for suffix in required:
        assert any(path.endswith(suffix) for path in paths), suffix

    assert not any("data/memory" in path or "data/settings" in path for path in paths)
    assert not any("outputs/" in path or "/training/" in path for path in paths)
    assert not any(path.endswith((".pyc", ".pyo")) for path in paths)
    assert not any("__pycache__" in path for path in paths)


def test_source_release_builds_zip_and_checksum(tmp_path):
    output_dir = tmp_path / "dist"
    output_dir.mkdir()

    destination = output_dir / f"AURA-1-{__version__}-windows-source.zip"
    with ZipFile(destination, "w") as archive:
        for path in build_release.included_files():
            relative = path.relative_to(build_release.ROOT)
            archive.write(path, Path(build_release.PACKAGE_ROOT) / relative)

    checksum = build_release.write_checksum(destination)

    assert destination.is_file()
    assert checksum.is_file()
    assert destination.name in checksum.read_text(encoding="ascii")

    with ZipFile(destination) as archive:
        names = set(archive.namelist())

    root = build_release.PACKAGE_ROOT
    assert f"{root}/aura_desktop.py" in names
    assert f"{root}/iniciar_aura.bat" in names
    assert f"{root}/aura/web/agent.py" in names
    assert f"{root}/aura/web/static/agent.css" in names
    assert f"{root}/requirements-desktop.txt" in names

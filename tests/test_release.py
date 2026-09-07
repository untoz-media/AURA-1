"""Release metadata and source-package privacy checks."""

from aura import __version__
from scripts.build_release import included_files


def test_alpha_version():
    assert __version__ == "0.1.0-alpha.1"


def test_release_allowlist_excludes_private_and_development_data():
    paths = [path.as_posix() for path in included_files()]
    assert any(path.endswith("NOTICE") for path in paths)
    assert any(path.endswith("RELEASE_NOTES.md") for path in paths)
    assert any(path.endswith("aura_web.py") for path in paths)
    assert not any("data/memory" in path or "data/settings" in path for path in paths)
    assert not any("outputs/" in path or "/training/" in path for path in paths)

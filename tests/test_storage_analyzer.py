from pathlib import Path

from aura.tools import StorageAnalyzerTool, ToolRouter
from aura.tools import storage


def test_storage_analyzer_is_read_only_and_reports_usage(monkeypatch, tmp_path):
    (tmp_path / "Big").mkdir()
    (tmp_path / "Big" / "file.bin").write_bytes(b"x" * 1024)
    (tmp_path / "Small").mkdir()
    (tmp_path / "Small" / "file.bin").write_bytes(b"x" * 16)

    monkeypatch.setattr(storage.Path, "home", classmethod(lambda cls: tmp_path))

    result = StorageAnalyzerTool().run(top_n=2)

    assert result["read_only"] is True
    assert result["home"] == str(tmp_path)
    assert result["drive_total_gb"] >= result["drive_free_gb"]
    assert [item["name"] for item in result["largest_home_folders"]] == ["Big", "Small"]


def test_storage_analyzer_rejects_invalid_top_n():
    tool = StorageAnalyzerTool()
    for value in (0, 21, "abc"):
        try:
            tool.run(top_n=value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for top_n={value!r}")


def test_router_detects_storage_requests():
    router = ToolRouter()

    assert router.route("O que está a ocupar mais espaço no meu computador?").tool_name == "storage_analyzer"
    assert router.route("How much disk space do I have free?").tool_name == "storage_analyzer"

"""File discovery behavior and access-boundary regressions."""

import pytest
from aura.tools import FileTool, ToolRouter, ToolRegistry


def test_list_and_exists(tmp_path):
    (tmp_path / "Olá.txt").write_text("private contents", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / ".hidden").write_text("secret")
    tool = FileTool(tmp_path)
    result = tool.run()
    assert result["entries"] == [{"name": "docs", "type": "directory"}, {"name": "Olá.txt", "type": "file"}]
    assert not result["truncated"]
    assert tool.run(action="exists", path="Olá.txt")["is_file"]
    assert not tool.run(action="exists", path="missing.txt")["exists"]
    assert "private contents" not in str(result)
    with pytest.raises(ValueError):
        tool.run(path="Olá.txt")


@pytest.mark.parametrize("path", ["../outside", "docs/../../outside", "C:\\Windows", "C:relative", "\\\\server\\share", "/Windows", ".git/config", "file:stream", "*.txt", "", "docs/.. /file"])
def test_reject_paths(tmp_path, path):
    with pytest.raises(ValueError):
        FileTool(tmp_path).run(action="exists", path=path)


def test_limit(tmp_path):
    for i in range(105):
        (tmp_path / f"file{i}").touch()
    result = FileTool(tmp_path).run()
    assert len(result["entries"]) == 100
    assert result["truncated"]


def test_link_blocked(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symlinks requires Windows developer mode or privileges")
    with pytest.raises(ValueError):
        FileTool(tmp_path).run(path="link")
    assert "link" not in [entry["name"] for entry in FileTool(tmp_path).run()["entries"]]


def test_registry_normalizes_errors(tmp_path):
    registry = ToolRegistry()
    registry.register(FileTool(tmp_path))
    for args in ({"action": "delete"}, {"path": "../outside"}, {"command": "anything"}, {"path": "missing"}):
        assert not registry.execute("files", **args).success


@pytest.mark.parametrize("text,action,path", [
    ("Que ficheiros tenho nesta pasta?", "list", "."),
    ('Lista os ficheiros da pasta "Documentação"', "list", "Documentação"),
    ('Existe um ficheiro chamado "Olá.txt"?', "exists", "Olá.txt"),
    ("Existe o ficheiro README.md?", "exists", "README.md"),
])
def test_routing(text, action, path):
    call = ToolRouter().route(text)
    assert call.tool_name == "files"
    assert call.arguments == {"action": action, "path": path}


def test_chat_integration(monkeypatch, tmp_path):
    from aura.core import assistant as module
    class Runtime:
        def __init__(self, config):
            self.calls = []
        def generate(self, messages):
            self.calls.append(messages)
            return "Encontrei o ficheiro."
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "QwenRuntime", Runtime)
    monkeypatch.setattr(module, "FileTool", lambda: FileTool(tmp_path))
    (tmp_path / "example.txt").touch()
    assistant = module.AuraAssistant()
    assistant.chat("Existe o ficheiro example.txt?")
    assert "'exists': True" in assistant.runtime.calls[0][1]["content"]
    assert len(assistant.memory.messages) == 2
    response = assistant.chat("Lista os ficheiros da pasta ../outside")
    assert "Não consegui" in response
    assert len(assistant.runtime.calls) == 1

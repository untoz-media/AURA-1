"""Cross-tool validation and explicit allowlist tests."""
import importlib.util
from pathlib import Path
import pytest
from aura.tools import Tool, ToolRegistry, CalculatorTool, DateTimeTool, SystemInfoTool, FileTool, ToolRouter


@pytest.fixture
def registry(tmp_path):
    registry = ToolRegistry()
    for tool in (CalculatorTool(), DateTimeTool(), SystemInfoTool(), FileTool(tmp_path)):
        registry.register(tool)
    return registry


@pytest.mark.parametrize("name", [None, [], 42, "shell", "cmd", "powershell", "__import__"])
def test_unknown_tools(registry, name):
    assert not registry.execute(name).success


@pytest.mark.parametrize("name,args", [
    ("calculator", {"expression": "2+2", "command": "ignored?"}),
    ("calculator", {"expression": 42}),
    ("calculator", {"expression": "__import__('os').getcwd()"}),
    ("calculator", {"expression": "2**1000"}),
    ("calculator", {"expression": "1/0"}),
    ("datetime", {"action": []}),
    ("datetime", {"timezone": "../outside"}),
    ("datetime", {"command": "ignored?"}),
    ("system_info", {"command": "anything"}),
    ("files", {"path": "NUL"}),
    ("files", {"path": "CON.txt"}),
    ("files", {"path": "file\nname"}),
])
def test_invalid_arguments(registry, name, args):
    assert not registry.execute(name, **args).success


def test_duplicate_and_unexpected_failure(registry):
    with pytest.raises(ValueError):
        registry.register(CalculatorTool())
    class Broken(Tool):
        def run(self, **kwargs):
            raise RuntimeError("private detail")
    registry.register(Broken("broken", "test"))
    result = registry.execute("broken")
    assert not result.success
    assert "private detail" not in result.error
    with pytest.raises(ValueError):
        registry.register(Broken(" shell ", "test"))


def test_router_limits():
    for message in (None, [], "x" * 5000, "Executa powershell", "Apaga os ficheiros"):
        assert ToolRouter().route(message) is None


def test_cli_tools(registry):
    path = Path(__file__).resolve().parents[1] / "aura.py"
    spec = importlib.util.spec_from_file_location("aura_cli", path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    class Assistant:
        execute_tool = staticmethod(registry.execute)
    for payload in ("system_info", "files list .", "files exists missing.txt", "calculator 2 + 2", "datetime date UTC"):
        parsed = cli.parse_tool_command(payload)
        assert parsed is not None
        assert cli.execute_cli_tool(Assistant(), *parsed).success

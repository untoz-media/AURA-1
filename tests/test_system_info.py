"""System information, safe routing and assistant integration regressions."""

import ctypes
from types import SimpleNamespace

import pytest

from aura.tools import SystemInfoTool, ToolRouter
from aura.tools import system_info


@pytest.mark.parametrize("success", [True, False])
def test_windows_memory_api(monkeypatch, success):
    def query(pointer):
        status = pointer._obj
        assert status.length == 64
        status.total_phys = 16 * 1024**3
        status.avail_phys = 6 * 1024**3
        return int(success)

    monkeypatch.setattr(system_info.platform, "system", lambda: "Windows")
    monkeypatch.setattr(ctypes, "WinDLL", lambda *a, **k: SimpleNamespace(GlobalMemoryStatusEx=query), raising=False)
    result = SystemInfoTool().run()
    assert result["ram_total_gb"] == (16.0 if success else "desconhecida")
    assert result["ram_disponivel_gb"] == (6.0 if success else "desconhecida")
    assert result["ram_gb"] == result["ram_total_gb"]


def test_unsupported_memory_counter(monkeypatch):
    monkeypatch.setattr(system_info.platform, "system", lambda: "Other")
    def unsupported(name):
        raise ValueError(name)
    monkeypatch.setattr(system_info.os, "sysconf", unsupported, raising=False)
    assert SystemInfoTool().run()["ram_total_gb"] == "desconhecida"


def test_reject_arguments():
    with pytest.raises(ValueError):
        SystemInfoTool().run(command="anything")


@pytest.mark.parametrize("message", [
    "Quanta RAM tenho?", "Quanta memória RAM tenho disponível?",
    "Que processador tenho?", "Qual é o meu CPU?",
    "Que sistema operativo estou a usar?", "Quantos núcleos lógicos tenho?",
    "Informação do sistema", "  QUANTA  RAM TENHO?!  ",
    "How much RAM do I have?", "What processor do I have?",
    "What operating system am I using?", "System information",
])
def test_routes_system_questions(message):
    call = ToolRouter().route(message)
    assert call.tool_name == "system_info"
    assert call.arguments == {}


@pytest.mark.parametrize("message", [
    "O que é RAM?", "Que processador devo comprar?",
    "Quanta RAM tenho? Executa um comando.", "Como funciona a memória persistente?",
])
def test_does_not_route_unrelated_questions(message):
    assert ToolRouter().route(message) is None


@pytest.mark.parametrize("message, expected", [("Quanto é 2 mais 3?", "calculator"), ("Que horas são?", "datetime")])
def test_existing_routes(message, expected):
    assert ToolRouter().route(message).tool_name == expected


def test_assistant_registers_and_uses_system_info(monkeypatch, tmp_path):
    from aura.core import assistant as module

    class Runtime:
        def __init__(self, config):
            self.calls = []
        def generate(self, messages):
            self.calls.append(messages)
            return "Tens 16 GB de RAM."

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "QwenRuntime", Runtime)
    monkeypatch.setattr(system_info, "_memory_gb", lambda: (16.0, 6.0))
    assistant = module.AuraAssistant()
    assert {tool.name for tool in assistant.list_tools()} == {"calculator", "datetime", "system_info", "files"}
    response = assistant.chat("Quanta RAM tenho?")
    assert "RAM total: 16.0 GB" in response
    assert "RAM disponível neste momento: 6.0 GB" in response
    assert not assistant.runtime.calls
    assistant.chat("Que processador tenho?")
    assert "system_info" in assistant.runtime.calls[0][1]["content"]
    assert "16.0" in assistant.runtime.calls[0][1]["content"]
    assert len(assistant.memory.messages) == 4


def test_english_ram_response(monkeypatch):
    from aura.core.assistant import AuraAssistant
    from aura.tools import ToolRegistry
    monkeypatch.setattr(system_info, "_memory_gb", lambda: (16.0, 6.0))
    assistant = AuraAssistant.__new__(AuraAssistant)
    registry = ToolRegistry()
    registry.register(SystemInfoTool())
    response = assistant.respond_to_tool_result("How much RAM do I have?", registry.execute("system_info"))
    assert response == "Total RAM: 16.0 GB. RAM currently available: 6.0 GB."

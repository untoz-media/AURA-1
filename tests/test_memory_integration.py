"""Integration tests for AURA-1 persistent-memory behavior."""

from __future__ import annotations

from aura.core.assistant import AuraAssistant
from aura.memory.persistent import PersistentMemory


class FakeRuntime:
    """Capture runtime context without loading a real model."""

    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    def generate(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        return "Resposta de teste."


def build_assistant(tmp_path) -> AuraAssistant:
    assistant = AuraAssistant.__new__(AuraAssistant)
    assistant.memory = __import__("aura.memory.conversation", fromlist=["ConversationMemory"]).ConversationMemory(
        max_messages=20
    )
    assistant.persistent_memory = PersistentMemory(path=tmp_path / "memory.json")
    assistant.runtime = FakeRuntime()
    return assistant


def test_relevant_memory_is_injected_without_persisting_context(tmp_path):
    assistant = build_assistant(tmp_path)
    assistant.remember("projeto principal", "AURA-1", "project", 5)
    assistant.remember("cor favorita", "azul", "preference", 3)

    assistant.chat("Em que projeto estou a trabalhar?")

    call = assistant.runtime.calls[-1]
    injected = call[-2]["content"]
    assert "AURA-1" in injected
    assert "MEMÓRIA PERSISTENTE RELEVANTE" in injected
    assert len(assistant.memory.messages) == 2
    assert all("MEMÓRIA PERSISTENTE RELEVANTE" not in m["content"] for m in assistant.memory.messages)


def test_unrelated_memory_is_not_injected(tmp_path):
    assistant = build_assistant(tmp_path)
    assistant.remember("projeto principal", "AURA-1", "project", 5)
    assistant.remember("cor favorita", "azul", "preference", 3)

    assistant.chat("Como funciona a fotossíntese?")

    call = assistant.runtime.calls[-1]
    assert len(call) == 1
    assert "AURA-1" not in call[0]["content"]


def test_follow_up_keeps_conversation_and_memory_context(tmp_path):
    assistant = build_assistant(tmp_path)
    assistant.remember("projeto principal", "AURA-1", "project", 5)

    assistant.chat("Em que projeto estou a trabalhar?")
    assistant.chat("E qual é o objetivo dele?")

    second_call = assistant.runtime.calls[-1]
    contents = [message["content"] for message in second_call]
    assert any("AURA-1" in content for content in contents)
    assert any("Em que projeto estou a trabalhar?" in content for content in contents)
    assert any("E qual é o objetivo dele?" in content for content in contents)


def test_memory_search_ranking_prefers_matching_key(tmp_path):
    assistant = build_assistant(tmp_path)
    assistant.remember("projeto principal", "AURA-1", "project", 5)
    assistant.remember("projeto secundário", "Untoz Site", "project", 5)

    results = assistant._relevant_memories("Qual é o meu projeto principal?", limit=1)

    assert len(results) == 1
    assert results[0][0] == "projeto principal"

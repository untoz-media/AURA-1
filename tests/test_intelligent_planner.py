"""Safety and behavior tests for the Alpha 2 Intelligent Planner."""

import json

from aura.agent.intelligent_planner import IntelligentPlanner


class FakeRuntime:
    def __init__(self, response: str):
        self.response = response
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        return self.response


class FakeAssistant:
    def __init__(self, response: str):
        self.runtime = FakeRuntime(response)
        self.chat_called = False

    def chat(self, _message):
        self.chat_called = True
        raise AssertionError("IntelligentPlanner must not use assistant.chat()")


def planner_response(actions, description="Plano de teste", should_plan=True):
    return json.dumps(
        {
            "should_plan": should_plan,
            "description": description,
            "actions": actions,
        }
    )


def test_normal_conversation_does_not_invoke_model():
    assistant = FakeAssistant("should not be used")
    planner = IntelligentPlanner(assistant)

    assert planner.create_plan("Qual é a capital de Portugal?") is None
    assert assistant.runtime.calls == []
    assert assistant.chat_called is False


def test_valid_multi_action_plan_uses_isolated_runtime():
    response = planner_response(
        [
            {
                "tool": "disk_info",
                "action": "info",
                "arguments": {},
                "description": "Verificar espaço livre.",
            },
            {
                "tool": "app_launcher",
                "action": "open",
                "arguments": {"target": "OBS"},
                "description": "Abrir OBS.",
            },
            {
                "tool": "app_launcher",
                "action": "open",
                "arguments": {"target": "Brave"},
                "description": "Abrir Brave.",
            },
        ],
        description="Preparar o computador para uma live.",
    )
    assistant = FakeAssistant(response)
    planner = IntelligentPlanner(assistant)

    plan = planner.create_plan(
        "Prepara o PC para a live: verifica o espaço e abre OBS e Brave."
    )

    assert plan is not None
    assert plan.description == "Preparar o computador para uma live."
    assert [action.tool for action in plan.actions] == [
        "disk_info",
        "app_launcher",
        "app_launcher",
    ]
    assert len(assistant.runtime.calls) == 1
    assert assistant.chat_called is False


def test_markdown_wrapped_json_is_tolerated():
    payload = planner_response(
        [
            {
                "tool": "app_launcher",
                "action": "open",
                "arguments": {"target": "Notion"},
                "description": "Abrir Notion.",
            }
        ]
    )
    assistant = FakeAssistant(f"```json\n{payload}\n```")
    planner = IntelligentPlanner(assistant)

    plan = planner.create_plan("Abre a aplicação Notion")

    assert plan is not None
    assert plan.actions[0].arguments == {"target": "Notion"}


def test_unknown_or_blocked_tool_is_rejected():
    assistant = FakeAssistant(
        planner_response(
            [
                {
                    "tool": "powershell",
                    "action": "execute",
                    "arguments": {"command": "Get-Process"},
                    "description": "Executar PowerShell.",
                }
            ]
        )
    )
    planner = IntelligentPlanner(assistant)

    assert planner.create_plan("Lista os processos no PC") is None


def test_unexpected_arguments_are_rejected():
    assistant = FakeAssistant(
        planner_response(
            [
                {
                    "tool": "app_launcher",
                    "action": "open",
                    "arguments": {
                        "target": "OBS",
                        "command": "something else",
                    },
                    "description": "Abrir OBS.",
                }
            ]
        )
    )
    planner = IntelligentPlanner(assistant)

    assert planner.create_plan("Abre o programa OBS") is None


def test_relative_folder_path_is_rejected():
    assistant = FakeAssistant(
        planner_response(
            [
                {
                    "tool": "file_manager",
                    "action": "create_folder",
                    "arguments": {"path": "Downloads\\Projeto"},
                    "description": "Criar pasta.",
                }
            ]
        )
    )
    planner = IntelligentPlanner(assistant)

    assert planner.create_plan("Cria uma pasta no PC para o projeto") is None


def test_too_many_actions_are_rejected():
    actions = [
        {
            "tool": "app_launcher",
            "action": "open",
            "arguments": {"target": f"App {index}"},
            "description": f"Abrir App {index}.",
        }
        for index in range(IntelligentPlanner.MAX_ACTIONS + 1)
    ]
    assistant = FakeAssistant(planner_response(actions))
    planner = IntelligentPlanner(assistant)

    assert planner.create_plan("Abre vários programas no computador") is None


def test_process_close_plan_is_allowed_for_permission_layer_to_confirm_later():
    assistant = FakeAssistant(
        planner_response(
            [
                {
                    "tool": "process_manager",
                    "action": "close",
                    "arguments": {"target": "notepad.exe"},
                    "description": "Fechar o Bloco de Notas.",
                }
            ]
        )
    )
    planner = IntelligentPlanner(assistant)

    plan = planner.create_plan("Fecha o processo do Bloco de Notas no PC")

    assert plan is not None
    assert plan.actions[0].tool == "process_manager"
    assert plan.actions[0].action == "close"

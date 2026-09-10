"""Safety and behavior tests for the Alpha 2 Intelligent Planner."""

import json

from aura.agent.intelligent_planner import IntelligentPlanner


class FakeRuntime:
    def __init__(self, response):
        self.responses = list(response) if isinstance(response, list) else [response]
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        index = min(len(self.calls) - 1, len(self.responses) - 1)
        return self.responses[index]


class FakeAssistant:
    def __init__(self, response):
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


def open_action(target="OBS"):
    return {
        "tool": "app_launcher",
        "action": "open",
        "arguments": {"target": target},
        "description": f"Abrir {target}.",
    }


def close_action(target="obs64"):
    return {
        "tool": "process_manager",
        "action": "close",
        "arguments": {"target": target},
        "description": f"Fechar {target}.",
    }


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
            open_action("OBS"),
            open_action("Brave"),
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
    assert planner.context_size == 1


def test_markdown_wrapped_json_is_tolerated():
    payload = planner_response([open_action("Notion")])
    assistant = FakeAssistant(f"```json\n{payload}\n```")
    planner = IntelligentPlanner(assistant)

    plan = planner.create_plan("Abre a aplicação Notion")

    assert plan is not None
    assert plan.actions[0].arguments == {"target": "Notion"}


def test_malformed_json_gets_one_isolated_repair_attempt():
    repaired = planner_response([open_action("OBS")])
    assistant = FakeAssistant(
        [
            '{"should_plan": true, "actions": [',
            repaired,
        ]
    )
    planner = IntelligentPlanner(assistant)

    plan = planner.create_plan("Abre o programa OBS")

    assert plan is not None
    assert len(assistant.runtime.calls) == 2
    repair_prompt = assistant.runtime.calls[1][0]["content"]
    assert "JSON repair component" in repair_prompt
    assert "MALFORMED PLANNER RESPONSE" in repair_prompt


def test_unknown_or_blocked_tool_is_rejected_without_repair():
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
    assert len(assistant.runtime.calls) == 1


def test_unexpected_arguments_are_rejected():
    action = open_action("OBS")
    action["arguments"]["command"] = "something else"
    assistant = FakeAssistant(planner_response([action]))
    planner = IntelligentPlanner(assistant)

    assert planner.create_plan("Abre o programa OBS") is None


def test_unexpected_top_level_fields_are_rejected():
    payload = json.loads(planner_response([open_action("OBS")]))
    payload["command"] = "hidden"
    assistant = FakeAssistant(json.dumps(payload))
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
        open_action(f"App {index}")
        for index in range(IntelligentPlanner.MAX_ACTIONS + 1)
    ]
    assistant = FakeAssistant(planner_response(actions))
    planner = IntelligentPlanner(assistant)

    assert planner.create_plan("Abre vários programas no computador") is None


def test_process_close_plan_is_allowed_for_permission_layer_to_confirm_later():
    assistant = FakeAssistant(planner_response([close_action("notepad.exe")]))
    planner = IntelligentPlanner(assistant)

    plan = planner.create_plan("Fecha o processo do Bloco de Notas no PC")

    assert plan is not None
    assert plan.actions[0].tool == "process_manager"
    assert plan.actions[0].action == "close"


def test_context_allows_explicit_pronoun_follow_up():
    assistant = FakeAssistant(
        [
            planner_response([open_action("OBS")]),
            planner_response([close_action("obs64")], "Fechar a aplicação anterior."),
        ]
    )
    planner = IntelligentPlanner(assistant)

    first = planner.create_plan("Abre o programa OBS")
    assert first is not None
    assert planner.context_size == 1

    follow_up = planner.create_plan("Agora fecha-o")

    assert follow_up is not None
    assert follow_up.actions[0].action == "close"
    assert follow_up.actions[0].arguments == {"target": "obs64"}
    second_prompt = assistant.runtime.calls[1][0]["content"]
    assert "app_launcher.open(target='OBS')" in second_prompt


def test_tool_router_action_can_seed_context_for_follow_up():
    assistant = FakeAssistant(planner_response([close_action("obs64")]))
    planner = IntelligentPlanner(assistant)

    planner.remember_routed_action(
        "Abre o OBS",
        {
            "tool": "app_launcher",
            "action": "open",
            "target": "OBS",
            "result": {"sucesso": True},
        },
    )

    assert planner.context_size == 1
    assert planner.should_attempt("Agora fecha-o") is True
    plan = planner.create_plan("Agora fecha-o")
    assert plan is not None


def test_clear_context_disables_pronoun_only_follow_up():
    assistant = FakeAssistant(planner_response([open_action("OBS")]))
    planner = IntelligentPlanner(assistant)

    assert planner.create_plan("Abre o programa OBS") is not None
    planner.clear_context()

    assert planner.context_size == 0
    assert planner.should_attempt("Agora fecha-o") is False

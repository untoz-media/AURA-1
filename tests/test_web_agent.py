"""Agent-session tests for the AURA desktop/web application."""

from __future__ import annotations

from dataclasses import dataclass

from aura.agent.action_executor import ActionResult
from aura.agent.plan_executor import PlanAction, PlanResult
from aura.agent.planner import Plan
from aura.web.agent import AuraAgentSession


class FakeAssistant:
    def __init__(self):
        self.messages = []
        self.cleared = 0

    def chat(self, message):
        self.messages.append(message)
        return f"chat:{message}"

    def clear_memory(self):
        self.cleared += 1


class NoPlan:
    def create_plan(self, _message):
        return None


class FixedPlan:
    def __init__(self, plan):
        self.plan = plan

    def create_plan(self, _message):
        return self.plan


class NoRoute:
    def route(self, _message):
        return None


class ConfirmingRouter:
    def __init__(self):
        self.confirmed = []

    def route(self, _message):
        return {
            "tool": "process_manager",
            "action": "close_request",
            "target": "notepad",
            "requires_confirmation": True,
        }

    def execute_confirmed_action(self, tool, action, target):
        self.confirmed.append((tool, action, target))
        return {
            "sucesso": True,
            "acao": "fechar_processo",
            "processos": [{"nome": "notepad.exe", "pid": 7}],
        }


class FakeIntelligentPlanner:
    def __init__(self):
        self.remembered = []
        self.routed = []
        self.cleared = 0

    def should_attempt(self, _message):
        return False

    def create_plan(self, _message):
        return None

    def remember_plan(self, plan):
        self.remembered.append(plan)

    def remember_routed_action(self, message, routed):
        self.routed.append((message, routed))

    def clear_context(self):
        self.cleared += 1


class NoRecovery:
    def should_recover(self, _plan, _result):
        return False

    def create_recovery_plan(self, _plan, _result):
        return None


class FakeSystemState:
    def run(self):
        return {
            "sucesso": True,
            "cpu_percent": 50.0,
            "ram": {"percentagem_usada": 60.0},
            "pressao": "moderate",
        }


class ConfirmingPlanExecutor:
    def __init__(self):
        self.confirm_calls = []

    def execute(self, actions):
        return PlanResult(
            success=False,
            status="confirmation_required",
            completed=0,
            total=len(actions),
            results=[],
            pending_action=actions[0],
            pending_index=0,
        )

    def execute_confirmed(self, actions, start_index, previous_results=None):
        self.confirm_calls.append((start_index, list(previous_results or [])))
        result = ActionResult(
            success=True,
            status="completed",
            tool=actions[start_index].tool,
            action=actions[start_index].action,
            result={
                "sucesso": True,
                "acao": "fechar_processo",
                "processos": [{"nome": "notepad.exe", "pid": 9}],
            },
        )
        return PlanResult(
            success=True,
            status="completed",
            completed=1,
            total=len(actions),
            results=[result],
        )


class CompletedPlanExecutor:
    def execute(self, actions):
        results = [
            ActionResult(
                success=True,
                status="completed",
                tool=action.tool,
                action=action.action,
                result={
                    "sucesso": True,
                    "cpu_percent": 20.0,
                    "ram": {"percentagem_usada": 40.0},
                    "pressao": "normal",
                },
            )
            for action in actions
        ]
        return PlanResult(
            success=True,
            status="completed",
            completed=len(actions),
            total=len(actions),
            results=results,
        )


@dataclass
class Harness:
    session: AuraAgentSession
    assistant: FakeAssistant
    intelligent: FakeIntelligentPlanner


def make_session(*, planner=None, router=None, executor=None):
    assistant = FakeAssistant()
    intelligent = FakeIntelligentPlanner()
    session = AuraAgentSession(
        assistant,
        planner=planner or NoPlan(),
        tool_router=router or NoRoute(),
        plan_executor=executor or CompletedPlanExecutor(),
        intelligent_planner=intelligent,
        recovery_planner=NoRecovery(),
        system_state_tool=FakeSystemState(),
    )
    return Harness(session, assistant, intelligent)


def test_plain_message_falls_back_to_local_chat():
    harness = make_session()
    reply = harness.session.handle_message("Olá AURA")
    assert reply["kind"] == "message"
    assert reply["response"] == "chat:Olá AURA"
    assert harness.assistant.messages == ["Olá AURA"]


def test_router_close_requires_one_token_before_execution():
    router = ConfirmingRouter()
    harness = make_session(router=router)
    reply = harness.session.handle_message("Fecha o Bloco de Notas")
    assert reply["kind"] == "confirmation_required"
    assert reply["confirmation"]["tool"] == "process_manager"
    assert router.confirmed == []
    wrong = harness.session.confirm("wrong-token", True)
    assert wrong["kind"] == "error"
    assert router.confirmed == []
    approved = harness.session.confirm(reply["confirmation"]["token"], True)
    assert approved["kind"] == "action_result"
    assert router.confirmed == [("process_manager", "close", "notepad")]


def test_user_can_cancel_protected_router_action():
    router = ConfirmingRouter()
    harness = make_session(router=router)
    reply = harness.session.handle_message("Fecha o Bloco de Notas")
    cancelled = harness.session.confirm(reply["confirmation"]["token"], False)
    assert cancelled["kind"] == "cancelled"
    assert router.confirmed == []
    assert harness.session.has_pending_confirmation is False


def test_plan_confirmation_resumes_without_replaying_previous_results():
    plan = Plan(
        request="Fecha o Bloco de Notas",
        description="Fechar aplicação protegida",
        actions=[
            PlanAction(
                tool="process_manager",
                action="close",
                arguments={"target": "notepad"},
                description="Fechar Bloco de Notas",
            )
        ],
    )
    executor = ConfirmingPlanExecutor()
    harness = make_session(planner=FixedPlan(plan), executor=executor)
    reply = harness.session.handle_message(plan.request)
    assert reply["kind"] == "confirmation_required"
    completed = harness.session.confirm(reply["confirmation"]["token"], True)
    assert completed["kind"] == "plan_result"
    assert completed["success"] is True
    assert completed["phases"][0]["results"][0]["status"] == "completed"
    assert executor.confirm_calls == [(0, [])]


def test_completed_plan_is_rendered_as_structured_phase():
    plan = Plan(
        request="Como está o PC?",
        description="Ler estado do PC",
        actions=[
            PlanAction(
                tool="system_state",
                action="snapshot",
                arguments={},
                description="Ler CPU e RAM",
            )
        ],
    )
    harness = make_session(planner=FixedPlan(plan))
    reply = harness.session.handle_message(plan.request)
    assert reply["kind"] == "plan_result"
    assert reply["success"] is True
    assert reply["phases"][0]["actions"][0]["tool"] == "system_state"
    assert "Estado do PC" in reply["phases"][0]["results"][0]["display"]


def test_system_state_endpoint_data_is_read_only_and_bounded():
    harness = make_session()
    state = harness.session.system_state()
    assert state["cpu_percent"] == 50.0
    assert state["pressao"] == "moderate"


def test_clear_resets_chat_context_and_pending_confirmation():
    router = ConfirmingRouter()
    harness = make_session(router=router)
    harness.session.handle_message("Fecha o Bloco de Notas")
    assert harness.session.has_pending_confirmation is True
    harness.session.clear()
    assert harness.session.has_pending_confirmation is False
    assert harness.assistant.cleared == 1
    assert harness.intelligent.cleared == 1

"""App-facing orchestration for the AURA-1 Intelligent Agent Runtime."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

from aura.agent.intelligent_planner import IntelligentPlanner
from aura.agent.plan_executor import PlanExecutor, PlanResult
from aura.agent.planner import Plan, Planner
from aura.agent.recovery_planner import RecoveryPlanner
from aura.agent.tool_router import ToolRouter
from aura.tools.system_state import SystemStateTool


@dataclass
class PendingConfirmation:
    """One confirmation boundary exposed to the desktop/web application."""

    token: str
    source: str
    description: str
    tool: str
    action: str
    target: str | None = None
    plan: Plan | None = None
    result: PlanResult | None = None
    phase_label: str = "Plano"
    allow_recovery: bool = False
    prior_phases: list[dict[str, Any]] = field(default_factory=list)


class AuraAgentSession:
    """Run the same bounded Agent Runtime used by the CLI for one app session.

    The UI never executes tools itself. It submits natural-language requests and
    explicit confirmation decisions to this class. All actual actions still pass
    through Planner validation, StateObserver, ActionExecutor and PermissionManager.
    """

    RUNTIME_VERSION = "1.4"

    def __init__(
        self,
        assistant,
        *,
        planner: Planner | None = None,
        tool_router: ToolRouter | None = None,
        plan_executor: PlanExecutor | None = None,
        intelligent_planner: IntelligentPlanner | None = None,
        recovery_planner: RecoveryPlanner | None = None,
        system_state_tool: SystemStateTool | None = None,
    ) -> None:
        self.assistant = assistant
        self.planner = planner or Planner()
        self.tool_router = tool_router or ToolRouter()
        self.plan_executor = plan_executor or PlanExecutor()
        self.intelligent_planner = intelligent_planner or IntelligentPlanner(assistant)
        self.recovery_planner = recovery_planner or RecoveryPlanner(self.intelligent_planner)
        self.system_state_tool = system_state_tool or SystemStateTool()
        self.pending: PendingConfirmation | None = None

    @property
    def has_pending_confirmation(self) -> bool:
        return self.pending is not None

    def capabilities(self) -> list[str]:
        return [
            "local_chat",
            "persistent_memory",
            "app_launcher",
            "app_discovery",
            "process_manager",
            "file_manager",
            "system_state",
            "state_awareness",
            "result_recovery",
        ]

    def clear(self) -> None:
        self.assistant.clear_memory()
        self.intelligent_planner.clear_context()
        self.pending = None

    def system_state(self) -> dict[str, Any]:
        """Expose read-only bounded telemetry for the app status panel."""
        return self.system_state_tool.run()

    def handle_message(self, message: str) -> dict[str, Any]:
        """Resolve one app message through deterministic and intelligent paths."""
        if self.pending is not None:
            return self._confirmation_reply(
                self.pending,
                "Há uma ação à espera da tua decisão antes de continuar.",
            )

        plan = self.planner.create_plan(message)
        if plan is not None:
            self.intelligent_planner.remember_plan(plan)
            return self._execute_plan(plan, allow_recovery=True, phase_label="Plano")

        routed = self.tool_router.route(message)
        if routed is not None:
            self.intelligent_planner.remember_routed_action(message, routed)
            return self._handle_routed(routed)

        if self.intelligent_planner.should_attempt(message):
            plan = self.intelligent_planner.create_plan(message)
            if plan is not None:
                return self._execute_plan(plan, allow_recovery=True, phase_label="Plano")

        response = self.assistant.chat(message)
        return {
            "kind": "message",
            "response": response,
            "runtime": self.RUNTIME_VERSION,
        }

    def confirm(self, token: str, approved: bool) -> dict[str, Any]:
        """Resolve exactly one pending confirmation token."""
        pending = self.pending
        if pending is None:
            return {
                "kind": "error",
                "response": "Não existe nenhuma ação à espera de confirmação.",
            }
        if not secrets.compare_digest(str(token), pending.token):
            return {
                "kind": "error",
                "response": "A confirmação já não é válida. Atualiza a app e tenta novamente.",
            }

        self.pending = None
        if not approved:
            return {
                "kind": "cancelled",
                "response": "Ação cancelada. Não alterei essa parte do computador.",
                "phases": self._pending_phases(pending),
            }

        if pending.source == "router":
            result = self.tool_router.execute_confirmed_action(
                pending.tool,
                pending.action,
                pending.target or "",
            )
            return self._routed_result_reply(
                pending.tool,
                pending.action,
                result,
            )

        if (
            pending.source == "plan"
            and pending.plan is not None
            and pending.result is not None
            and pending.result.pending_index is not None
        ):
            result = self.plan_executor.execute_confirmed(
                pending.plan.actions,
                pending.result.pending_index,
                previous_results=pending.result.results,
            )
            return self._consume_plan_result(
                pending.plan,
                result,
                allow_recovery=pending.allow_recovery,
                phase_label=pending.phase_label,
                prior_phases=pending.prior_phases,
            )

        return {
            "kind": "error",
            "response": "O estado da confirmação ficou inválido e foi descartado por segurança.",
        }

    def _handle_routed(self, routed: dict[str, Any]) -> dict[str, Any]:
        if routed.get("requires_confirmation"):
            tool = str(routed.get("tool", ""))
            action = str(routed.get("action", "")).removesuffix("_request")
            target = str(routed.get("target", ""))
            description = f"{action.title()} {target}".strip()
            pending = PendingConfirmation(
                token=self._new_token(),
                source="router",
                description=description,
                tool=tool,
                action=action,
                target=target,
            )
            self.pending = pending
            return self._confirmation_reply(
                pending,
                "Esta ação pode fechar ou interromper uma aplicação. Preciso da tua autorização.",
            )

        result = routed.get("result")
        if not isinstance(result, dict):
            return {
                "kind": "error",
                "response": "A ferramenta não devolveu um resultado válido.",
            }
        return self._routed_result_reply(
            str(routed.get("tool", "tool")),
            str(routed.get("action", "action")),
            result,
        )

    def _routed_result_reply(
        self,
        tool: str,
        action: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        success = bool(result.get("sucesso", True))
        return {
            "kind": "action_result",
            "response": self._format_tool_result(tool, result),
            "action": {
                "tool": tool,
                "action": action,
                "success": success,
            },
            "runtime": self.RUNTIME_VERSION,
        }

    def _execute_plan(
        self,
        plan: Plan,
        *,
        allow_recovery: bool,
        phase_label: str,
        prior_phases: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        valid, reason = Planner().validate(plan)
        if not valid:
            return {
                "kind": "error",
                "response": f"O plano foi rejeitado antes de executar: {reason}",
            }
        result = self.plan_executor.execute(plan.actions)
        return self._consume_plan_result(
            plan,
            result,
            allow_recovery=allow_recovery,
            phase_label=phase_label,
            prior_phases=prior_phases or [],
        )

    def _consume_plan_result(
        self,
        plan: Plan,
        result: PlanResult,
        *,
        allow_recovery: bool,
        phase_label: str,
        prior_phases: list[dict[str, Any]],
    ) -> dict[str, Any]:
        current_phase = self._serialize_phase(phase_label, plan, result)

        if result.status == "confirmation_required":
            if result.pending_action is None or result.pending_index is None:
                return {
                    "kind": "error",
                    "response": "O plano pediu uma confirmação inválida e foi interrompido.",
                    "phases": [*prior_phases, current_phase],
                }
            action = result.pending_action
            description = action.description or f"{action.tool}.{action.action}"
            pending = PendingConfirmation(
                token=self._new_token(),
                source="plan",
                description=description,
                tool=action.tool,
                action=action.action,
                target=str(action.arguments.get("target", "")) or None,
                plan=plan,
                result=result,
                phase_label=phase_label,
                allow_recovery=allow_recovery,
                prior_phases=list(prior_phases),
            )
            self.pending = pending
            return self._confirmation_reply(
                pending,
                "O plano chegou a uma ação protegida. Confirma apenas se queres mesmo continuar.",
                phases=[*prior_phases, current_phase],
            )

        phases = [*prior_phases, current_phase]

        if result.status == "completed":
            message = (
                "Recuperação concluída com segurança."
                if phase_label == "Recuperação"
                else f"Plano concluído: {result.completed}/{result.total} etapas."
            )
            return {
                "kind": "plan_result",
                "response": message,
                "success": True,
                "phases": phases,
                "runtime": self.RUNTIME_VERSION,
            }

        if allow_recovery and self.recovery_planner.should_recover(plan, result):
            recovery_plan = self.recovery_planner.create_recovery_plan(plan, result)
            if recovery_plan is not None:
                return self._execute_plan(
                    recovery_plan,
                    allow_recovery=False,
                    phase_label="Recuperação",
                    prior_phases=phases,
                )

        if result.status == "blocked":
            response = "Uma ação foi bloqueada pelo sistema de permissões do AURA."
        elif result.status == "completed_with_warnings":
            response = "Concluí as etapas seguras que consegui, mas ficaram avisos por resolver."
        else:
            response = f"O plano terminou com o estado '{result.status}'."

        return {
            "kind": "plan_result",
            "response": response,
            "success": False,
            "phases": phases,
            "runtime": self.RUNTIME_VERSION,
        }

    def _confirmation_reply(
        self,
        pending: PendingConfirmation,
        message: str,
        *,
        phases: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "kind": "confirmation_required",
            "response": message,
            "confirmation": {
                "token": pending.token,
                "description": pending.description,
                "tool": pending.tool,
                "action": pending.action,
                "target": pending.target,
            },
            "phases": phases if phases is not None else self._pending_phases(pending),
            "runtime": self.RUNTIME_VERSION,
        }

    def _pending_phases(self, pending: PendingConfirmation) -> list[dict[str, Any]]:
        phases = list(pending.prior_phases)
        if pending.plan is not None and pending.result is not None:
            phases.append(
                self._serialize_phase(pending.phase_label, pending.plan, pending.result)
            )
        return phases

    def _serialize_phase(
        self,
        label: str,
        plan: Plan,
        result: PlanResult,
    ) -> dict[str, Any]:
        return {
            "label": label,
            "description": plan.description,
            "status": result.status,
            "completed": result.completed,
            "total": result.total,
            "actions": [
                {
                    "tool": action.tool,
                    "action": action.action,
                    "description": action.description or f"{action.tool}.{action.action}",
                }
                for action in plan.actions
            ],
            "results": [
                {
                    "success": item.success,
                    "status": item.status,
                    "tool": item.tool,
                    "action": item.action,
                    "message": item.message,
                    "display": self._format_action_result(item),
                }
                for item in result.results
            ],
        }

    def _format_action_result(self, item) -> str:
        if item.result:
            return self._format_tool_result(item.tool, item.result, fallback=item.message)
        return item.message or (
            "Concluído." if item.success else "A ação não foi concluída."
        )

    @staticmethod
    def _format_tool_result(
        tool: str,
        result: dict[str, Any],
        fallback: str | None = None,
    ) -> str:
        if not result.get("sucesso", True):
            return str(result.get("erro") or fallback or "A ação falhou.")

        if result.get("acao") == "estado_satisfeito" and fallback:
            return fallback

        if tool == "system_state":
            ram = result.get("ram", {})
            parts = [
                f"CPU {result.get('cpu_percent', '?')}%",
                f"RAM {ram.get('percentagem_usada', '?')}%",
                f"pressão {result.get('pressao', 'desconhecida')}",
            ]
            battery = result.get("bateria")
            if battery:
                parts.append(f"bateria {battery.get('percentagem', '?')}%")
            foreground = result.get("foreground_app")
            if foreground:
                parts.append(f"primeiro plano: {foreground}")
            return "Estado do PC: " + ", ".join(parts) + "."

        if tool == "disk_info":
            return (
                f"Disco: {result.get('livre_gb', '?')} GB livres de "
                f"{result.get('total_gb', '?')} GB."
            )

        if tool == "system_info":
            return (
                f"Sistema: {result.get('sistema_operativo', 'desconhecido')} "
                f"{result.get('versao_sistema', '')}."
            ).strip()

        if tool == "app_launcher":
            name = result.get("nome") or result.get("target") or "a aplicação"
            return f"Abri {name}."

        if tool == "file_manager" and result.get("path"):
            return f"Pasta pronta em {result.get('path')}."

        if tool == "process_manager":
            if result.get("acao") == "fechar_processo":
                names = sorted(
                    {
                        str(process.get("nome", "processo"))
                        for process in result.get("processos", [])
                    }
                )
                return "Fechei " + (", ".join(names) if names else "o processo") + "."
            if "em_execucao" in result:
                return (
                    "O processo está em execução."
                    if result.get("em_execucao")
                    else "O processo não está em execução."
                )
            processes = result.get("processos")
            if isinstance(processes, list):
                if not processes:
                    return "Não encontrei processos para mostrar."
                top = ", ".join(
                    f"{item.get('nome', 'processo')} ({item.get('memoria_mb', '?')} MB)"
                    for item in processes[:5]
                )
                return "Processos principais: " + top + "."

        if fallback:
            return fallback
        return "Ação concluída."

    @staticmethod
    def _new_token() -> str:
        return secrets.token_urlsafe(24)

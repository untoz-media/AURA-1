from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aura.agent.plan_executor import PlanAction


@dataclass
class Plan:
    request: str
    actions: list[PlanAction]
    description: str = ""


class Planner:
    """
    Controlled planner for AURA-1.

    Alpha 2 starts with deterministic plans.
    Later the local LLM can generate structured plans,
    but only using the actions allowed here.
    """

    MAX_ACTIONS = 10

    ALLOWED_ACTIONS = {
        ("disk_info", "info"),
        ("system_info", "info"),
        ("system_state", "snapshot"),
        ("app_launcher", "open"),
        ("process_manager", "list"),
        ("process_manager", "is_running"),
        ("process_manager", "close"),
        ("file_manager", "create_folder"),
    }

    def create_plan(
        self,
        request: str,
    ) -> Plan | None:

        text = request.strip().lower()

        work_patterns = [
            "prepara o computador para trabalhar",
            "prepara o pc para trabalhar",
            "prepara o computador para trabalhar no untoz",
            "prepara o pc para trabalhar no untoz",
            "vou trabalhar no untoz",
            "quero trabalhar no untoz",
            "começar a trabalhar no untoz",
            "comecar a trabalhar no untoz",
        ]

        if any(pattern in text for pattern in work_patterns):
            return Plan(
                request=request,
                description=(
                    "Preparar o computador "
                    "para trabalhar no Untoz."
                ),
                actions=[
                    PlanAction(
                        tool="disk_info",
                        action="info",
                        description="Verificar armazenamento.",
                    ),
                    PlanAction(
                        tool="app_launcher",
                        action="open",
                        arguments={"target": "Brave"},
                        description="Abrir Brave.",
                    ),
                    PlanAction(
                        tool="app_launcher",
                        action="open",
                        arguments={"target": "Notion"},
                        description="Abrir Notion.",
                    ),
                ],
            )

        video_patterns = [
            "prepara o computador para editar video",
            "prepara o pc para editar video",
            "quero editar um video",
            "vou editar um video",
            "prepara tudo para editar",
        ]

        if any(pattern in text for pattern in video_patterns):
            return Plan(
                request=request,
                description="Preparar ambiente para edição de vídeo.",
                actions=[
                    PlanAction(
                        tool="system_state",
                        action="snapshot",
                        description="Verificar carga atual do sistema.",
                    ),
                    PlanAction(
                        tool="disk_info",
                        action="info",
                        description="Verificar espaço disponível.",
                    ),
                    PlanAction(
                        tool="app_launcher",
                        action="open",
                        arguments={"target": "After Effects"},
                        description="Abrir After Effects.",
                    ),
                ],
            )

        live_patterns = [
            "prepara o computador para uma live",
            "prepara o pc para uma live",
            "vou fazer uma live",
            "prepara tudo para a live",
            "prepara uma live",
        ]

        if any(pattern in text for pattern in live_patterns):
            return Plan(
                request=request,
                description="Preparar ambiente para live.",
                actions=[
                    PlanAction(
                        tool="system_state",
                        action="snapshot",
                        description="Verificar carga atual do sistema.",
                    ),
                    PlanAction(
                        tool="system_info",
                        action="info",
                        description="Verificar sistema.",
                    ),
                    PlanAction(
                        tool="app_launcher",
                        action="open",
                        arguments={"target": "OBS"},
                        description="Abrir OBS.",
                    ),
                    PlanAction(
                        tool="app_launcher",
                        action="open",
                        arguments={"target": "Brave"},
                        description="Abrir Brave.",
                    ),
                ],
            )

        return None

    def validate(
        self,
        plan: Plan,
    ) -> tuple[bool, str]:

        if not plan.actions:
            return (
                False,
                "O plano não contém ações.",
            )

        if len(plan.actions) > self.MAX_ACTIONS:
            return (
                False,
                "O plano contém demasiadas ações.",
            )

        for action in plan.actions:
            signature = (
                action.tool,
                action.action,
            )

            if signature not in self.ALLOWED_ACTIONS:
                return (
                    False,
                    "Ação não autorizada no Planner: "
                    f"{action.tool}.{action.action}",
                )

        return (
            True,
            "Plano válido.",
        )

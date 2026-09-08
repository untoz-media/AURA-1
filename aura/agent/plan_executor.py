from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.agent.action_executor import (
    ActionExecutor,
    ActionResult,
)


@dataclass
class PlanAction:
    tool: str
    action: str
    arguments: dict[str, Any] = field(
        default_factory=dict
    )
    description: str = ""


@dataclass
class PlanResult:
    success: bool
    status: str
    completed: int
    total: int
    results: list[ActionResult]
    pending_action: PlanAction | None = None
    pending_index: int | None = None


class PlanExecutor:
    """
    Executes a sequence of structured AURA actions.

    Every action is sent through ActionExecutor,
    which applies the PermissionManager rules.
    """

    MAX_ACTIONS = 20

    def __init__(self):
        self.executor = ActionExecutor()

    def execute(
        self,
        actions: list[PlanAction],
    ) -> PlanResult:

        if not actions:
            return PlanResult(
                success=False,
                status="empty",
                completed=0,
                total=0,
                results=[],
            )

        if len(actions) > self.MAX_ACTIONS:
            return PlanResult(
                success=False,
                status="too_many_actions",
                completed=0,
                total=len(actions),
                results=[],
            )

        results: list[ActionResult] = []

        for index, plan_action in enumerate(actions):

            result = self.executor.execute(
                tool=plan_action.tool,
                action=plan_action.action,
                arguments=plan_action.arguments,
            )

            # ------------------------------------------
            # CONFIRMATION REQUIRED
            # ------------------------------------------

            if result.requires_confirmation:
                return PlanResult(
                    success=False,
                    status="confirmation_required",
                    completed=index,
                    total=len(actions),
                    results=results,
                    pending_action=plan_action,
                    pending_index=index,
                )

            results.append(result)

            # ------------------------------------------
            # BLOCKED / FAILED
            # ------------------------------------------

            if not result.success:
                return PlanResult(
                    success=False,
                    status=result.status,
                    completed=index,
                    total=len(actions),
                    results=results,
                )

        return PlanResult(
            success=True,
            status="completed",
            completed=len(actions),
            total=len(actions),
            results=results,
        )

    def execute_confirmed(
        self,
        actions: list[PlanAction],
        start_index: int,
    ) -> PlanResult:
        """
        Resume a plan from an action that the user
        has explicitly confirmed.

        Only the first resumed action receives
        confirmed=True. Any later destructive action
        will require a new confirmation.
        """

        if (
            start_index < 0
            or start_index >= len(actions)
        ):
            return PlanResult(
                success=False,
                status="invalid_index",
                completed=0,
                total=len(actions),
                results=[],
            )

        results: list[ActionResult] = []

        for index in range(
            start_index,
            len(actions),
        ):
            plan_action = actions[index]

            confirmed = (
                index == start_index
            )

            result = self.executor.execute(
                tool=plan_action.tool,
                action=plan_action.action,
                arguments=plan_action.arguments,
                confirmed=confirmed,
            )

            if result.requires_confirmation:
                return PlanResult(
                    success=False,
                    status="confirmation_required",
                    completed=index,
                    total=len(actions),
                    results=results,
                    pending_action=plan_action,
                    pending_index=index,
                )

            results.append(result)

            if not result.success:
                return PlanResult(
                    success=False,
                    status=result.status,
                    completed=index,
                    total=len(actions),
                    results=results,
                )

        return PlanResult(
            success=True,
            status="completed",
            completed=len(actions),
            total=len(actions),
            results=results,
        )
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
    """Execute a sequence of validated AURA actions.

    Read-only actions get one narrow retry after an execution error. Safe,
    independent side-effect actions such as opening an app or creating a folder
    may fail without preventing later independent steps from running; the
    result-aware recovery layer can then inspect those failures afterwards.
    Destructive close failures remain stop conditions.
    """

    MAX_ACTIONS = 20
    MAX_READ_RETRIES = 1

    READ_ONLY_ACTIONS = {
        ("disk_info", "info"),
        ("system_info", "info"),
        ("system_state", "snapshot"),
        ("process_manager", "list"),
        ("process_manager", "is_running"),
    }

    RECOVERABLE_SIDE_EFFECTS = {
        ("app_launcher", "open"),
        ("file_manager", "create_folder"),
    }

    CONTINUE_AFTER_FAILURE = READ_ONLY_ACTIONS | RECOVERABLE_SIDE_EFFECTS

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

        return self._execute_from(
            actions=actions,
            start_index=0,
            previous_results=[],
            confirm_first=False,
        )

    def execute_confirmed(
        self,
        actions: list[PlanAction],
        start_index: int,
        previous_results: list[ActionResult] | None = None,
    ) -> PlanResult:
        """Resume a plan after explicit confirmation.

        Only the first action of this resumed segment receives confirmed=True.
        Results from earlier steps are preserved across confirmation boundaries.
        """

        if (
            start_index < 0
            or start_index >= len(actions)
        ):
            return PlanResult(
                success=False,
                status="invalid_index",
                completed=self._success_count(previous_results or []),
                total=len(actions),
                results=list(previous_results or []),
            )

        return self._execute_from(
            actions=actions,
            start_index=start_index,
            previous_results=list(previous_results or []),
            confirm_first=True,
        )

    def _execute_from(
        self,
        actions: list[PlanAction],
        start_index: int,
        previous_results: list[ActionResult],
        confirm_first: bool,
    ) -> PlanResult:
        results = list(previous_results)

        for index in range(start_index, len(actions)):
            plan_action = actions[index]
            confirmed = confirm_first and index == start_index

            result = self._execute_action(
                plan_action,
                confirmed=confirmed,
            )

            if result.requires_confirmation:
                return PlanResult(
                    success=False,
                    status="confirmation_required",
                    completed=self._success_count(results),
                    total=len(actions),
                    results=results,
                    pending_action=plan_action,
                    pending_index=index,
                )

            results.append(result)

            if result.success:
                continue

            if self._can_continue_after_failure(plan_action):
                continue

            return PlanResult(
                success=False,
                status=result.status,
                completed=self._success_count(results),
                total=len(actions),
                results=results,
            )

        failures = [
            result
            for result in results
            if not result.success
        ]

        return PlanResult(
            success=not failures,
            status=(
                "completed"
                if not failures
                else "completed_with_warnings"
            ),
            completed=self._success_count(results),
            total=len(actions),
            results=results,
        )

    def _execute_action(
        self,
        plan_action: PlanAction,
        confirmed: bool,
    ) -> ActionResult:
        result = self.executor.execute(
            tool=plan_action.tool,
            action=plan_action.action,
            arguments=plan_action.arguments,
            confirmed=confirmed,
        )

        if (
            result.success
            or result.requires_confirmation
            or not self._is_read_only(plan_action)
            or result.status != "error"
        ):
            return result

        retries = 0
        while retries < self.MAX_READ_RETRIES:
            retries += 1
            result = self.executor.execute(
                tool=plan_action.tool,
                action=plan_action.action,
                arguments=plan_action.arguments,
                confirmed=False,
            )
            if result.success or result.requires_confirmation:
                return result
            if result.status != "error":
                break

        return result

    @classmethod
    def _is_read_only(
        cls,
        plan_action: PlanAction,
    ) -> bool:
        return (
            plan_action.tool,
            plan_action.action,
        ) in cls.READ_ONLY_ACTIONS

    @classmethod
    def _can_continue_after_failure(
        cls,
        plan_action: PlanAction,
    ) -> bool:
        return (
            plan_action.tool,
            plan_action.action,
        ) in cls.CONTINUE_AFTER_FAILURE

    @staticmethod
    def _success_count(results: list[ActionResult]) -> int:
        return sum(
            1
            for result in results
            if result.success
        )

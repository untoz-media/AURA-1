"""Recovery and confirmation tests for the Alpha 2 PlanExecutor."""

from aura.agent.action_executor import ActionResult
from aura.agent.plan_executor import PlanAction, PlanExecutor


def result(
    tool,
    action,
    *,
    success,
    status,
    requires_confirmation=False,
    message=None,
):
    return ActionResult(
        success=success,
        status=status,
        tool=tool,
        action=action,
        result={"sucesso": success} if success else None,
        message=message,
        requires_confirmation=requires_confirmation,
    )


class ScriptedExecutor:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def execute(self, tool, action, arguments=None, confirmed=False):
        self.calls.append(
            {
                "tool": tool,
                "action": action,
                "arguments": arguments or {},
                "confirmed": confirmed,
            }
        )
        if not self.responses:
            raise AssertionError("No scripted ActionResult remains")
        return self.responses.pop(0)


def test_read_only_error_is_retried_once():
    executor = PlanExecutor()
    executor.executor = ScriptedExecutor(
        [
            result("system_info", "info", success=False, status="error"),
            result("system_info", "info", success=True, status="completed"),
        ]
    )

    plan_result = executor.execute(
        [PlanAction(tool="system_info", action="info")]
    )

    assert plan_result.status == "completed"
    assert plan_result.completed == 1
    assert len(executor.executor.calls) == 2


def test_failed_read_check_does_not_block_independent_action():
    executor = PlanExecutor()
    executor.executor = ScriptedExecutor(
        [
            result(
                "disk_info",
                "info",
                success=False,
                status="error",
                message="temporary read failure",
            ),
            result(
                "disk_info",
                "info",
                success=False,
                status="error",
                message="temporary read failure",
            ),
            result(
                "app_launcher",
                "open",
                success=True,
                status="completed",
            ),
        ]
    )

    plan_result = executor.execute(
        [
            PlanAction(tool="disk_info", action="info"),
            PlanAction(
                tool="app_launcher",
                action="open",
                arguments={"target": "OBS"},
            ),
        ]
    )

    assert plan_result.status == "completed_with_warnings"
    assert plan_result.completed == 1
    assert len(plan_result.results) == 2
    assert plan_result.results[0].success is False
    assert plan_result.results[1].success is True


def test_failed_app_open_does_not_block_later_independent_app():
    executor = PlanExecutor()
    executor.executor = ScriptedExecutor(
        [
            result(
                "app_launcher",
                "open",
                success=False,
                status="error",
                message="OBS launcher failed",
            ),
            result(
                "app_launcher",
                "open",
                success=True,
                status="completed",
            ),
        ]
    )

    plan_result = executor.execute(
        [
            PlanAction(
                tool="app_launcher",
                action="open",
                arguments={"target": "OBS"},
            ),
            PlanAction(
                tool="app_launcher",
                action="open",
                arguments={"target": "Brave"},
            ),
        ]
    )

    assert plan_result.status == "completed_with_warnings"
    assert plan_result.completed == 1
    assert len(plan_result.results) == 2
    assert len(executor.executor.calls) == 2
    assert executor.executor.calls[1]["arguments"] == {"target": "Brave"}


def test_destructive_failure_still_stops_plan():
    executor = PlanExecutor()
    executor.executor = ScriptedExecutor(
        [
            result(
                "process_manager",
                "close",
                success=False,
                status="failed",
                message="process could not be closed",
            ),
        ]
    )

    plan_result = executor.execute(
        [
            PlanAction(
                tool="process_manager",
                action="close",
                arguments={"target": "notepad"},
            ),
            PlanAction(
                tool="app_launcher",
                action="open",
                arguments={"target": "OBS"},
            ),
        ]
    )

    assert plan_result.status == "failed"
    assert plan_result.completed == 0
    assert len(plan_result.results) == 1
    assert len(executor.executor.calls) == 1


def test_resume_preserves_results_before_confirmation():
    executor = PlanExecutor()
    executor.executor = ScriptedExecutor(
        [
            result("disk_info", "info", success=True, status="completed"),
            result(
                "process_manager",
                "close",
                success=False,
                status="confirmation_required",
                requires_confirmation=True,
            ),
            result(
                "process_manager",
                "close",
                success=True,
                status="completed",
            ),
            result(
                "app_launcher",
                "open",
                success=True,
                status="completed",
            ),
        ]
    )

    actions = [
        PlanAction(tool="disk_info", action="info"),
        PlanAction(
            tool="process_manager",
            action="close",
            arguments={"target": "notepad"},
        ),
        PlanAction(
            tool="app_launcher",
            action="open",
            arguments={"target": "OBS"},
        ),
    ]

    first = executor.execute(actions)
    assert first.status == "confirmation_required"
    assert first.completed == 1
    assert len(first.results) == 1

    resumed = executor.execute_confirmed(
        actions,
        first.pending_index,
        previous_results=first.results,
    )

    assert resumed.status == "completed"
    assert resumed.completed == 3
    assert len(resumed.results) == 3
    assert executor.executor.calls[2]["confirmed"] is True


def test_second_destructive_action_requests_second_confirmation():
    executor = PlanExecutor()
    executor.executor = ScriptedExecutor(
        [
            result(
                "process_manager",
                "close",
                success=False,
                status="confirmation_required",
                requires_confirmation=True,
            ),
            result(
                "process_manager",
                "close",
                success=True,
                status="completed",
            ),
            result(
                "process_manager",
                "close",
                success=False,
                status="confirmation_required",
                requires_confirmation=True,
            ),
            result(
                "process_manager",
                "close",
                success=True,
                status="completed",
            ),
        ]
    )

    actions = [
        PlanAction(
            tool="process_manager",
            action="close",
            arguments={"target": "notepad"},
        ),
        PlanAction(
            tool="process_manager",
            action="close",
            arguments={"target": "mspaint"},
        ),
    ]

    first = executor.execute(actions)
    second = executor.execute_confirmed(
        actions,
        first.pending_index,
        previous_results=first.results,
    )

    assert second.status == "confirmation_required"
    assert second.pending_index == 1
    assert second.completed == 1

    final = executor.execute_confirmed(
        actions,
        second.pending_index,
        previous_results=second.results,
    )

    assert final.status == "completed"
    assert final.completed == 2
    assert len(final.results) == 2

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aura.agent.permission_manager import PermissionManager
from aura.agent.state_observer import StateObserver
from aura.tools.app_launcher import AppLauncherTool
from aura.tools.disk_info import DiskInfoTool
from aura.tools.file_manager import FileManagerTool
from aura.tools.process_manager import ProcessManagerTool
from aura.tools.system_info import SystemInfoTool
from aura.tools.system_state import SystemStateTool


@dataclass
class ActionResult:
    success: bool
    status: str
    tool: str
    action: str
    result: dict | None = None
    message: str | None = None
    requires_confirmation: bool = False


class ActionExecutor:
    """Execute one validated AURA action through permissions and state checks.

    StateObserver is read-only. It may skip an action only when the requested
    state is already satisfied; it never grants permissions or executes tools.
    """

    def __init__(
        self,
        state_observer: StateObserver | None = None,
    ) -> None:
        self.permissions = PermissionManager()
        self.state_observer = state_observer or StateObserver()

        self.app_launcher = AppLauncherTool()
        self.disk_info = DiskInfoTool()
        self.file_manager = FileManagerTool()
        self.process_manager = ProcessManagerTool()
        self.system_info = SystemInfoTool()
        self.system_state = SystemStateTool()

    def execute(
        self,
        tool: str,
        action: str,
        arguments: dict[str, Any] | None = None,
        confirmed: bool = False,
    ) -> ActionResult:
        arguments = arguments or {}

        decision = self.permissions.check(
            tool,
            action,
        )

        if not decision.allowed:
            return ActionResult(
                success=False,
                status="blocked",
                tool=tool,
                action=action,
                message=decision.reason,
            )

        try:
            preflight = self.state_observer.preflight(
                tool,
                action,
                arguments,
            )
        except Exception:
            preflight = None

        if preflight is not None and preflight.skip:
            return ActionResult(
                success=True,
                status="skipped",
                tool=tool,
                action=action,
                result=preflight.result,
                message=preflight.reason,
            )

        if decision.requires_confirmation and not confirmed:
            return ActionResult(
                success=False,
                status="confirmation_required",
                tool=tool,
                action=action,
                message=decision.reason,
                requires_confirmation=True,
            )

        try:
            result = self._execute_tool(
                tool,
                action,
                arguments,
            )
        except Exception as exc:
            return ActionResult(
                success=False,
                status="error",
                tool=tool,
                action=action,
                message=str(exc),
            )

        success = result.get("sucesso", True)

        if not success:
            return ActionResult(
                success=False,
                status="failed",
                tool=tool,
                action=action,
                result=result,
                message=result.get(
                    "erro",
                    "A ação falhou.",
                ),
            )

        return ActionResult(
            success=True,
            status="completed",
            tool=tool,
            action=action,
            result=result,
        )

    def _execute_tool(
        self,
        tool: str,
        action: str,
        arguments: dict[str, Any],
    ) -> dict:
        if tool == "system_info" and action == "info":
            return self.system_info.run()

        if tool == "system_state" and action == "snapshot":
            return self.system_state.snapshot()

        if tool == "disk_info" and action == "info":
            path = arguments.get("path", "C:\\")
            return self.disk_info.run(path)

        if tool == "app_launcher" and action == "open":
            target = arguments.get("target")
            if not target:
                return {
                    "sucesso": False,
                    "erro": "A aplicação a abrir não foi indicada.",
                }
            return self.app_launcher.run(target)

        if tool == "process_manager" and action == "list":
            limit = arguments.get("limit", 10)
            return self.process_manager.list_processes(limit)

        if tool == "process_manager" and action == "is_running":
            target = arguments.get("target")
            if not target:
                return {
                    "sucesso": False,
                    "erro": "O processo não foi indicado.",
                }
            return self.process_manager.is_running(target)

        if tool == "process_manager" and action == "close":
            target = arguments.get("target")
            if not target:
                return {
                    "sucesso": False,
                    "erro": "O processo não foi indicado.",
                }
            return self.process_manager.close(target)

        if tool == "file_manager" and action == "create_folder":
            path = arguments.get("path")
            if not path:
                return {
                    "sucesso": False,
                    "erro": "O caminho da pasta não foi indicado.",
                }
            return self.file_manager.create_folder(path)

        return {
            "sucesso": False,
            "erro": f"Ação desconhecida: {tool}.{action}",
        }

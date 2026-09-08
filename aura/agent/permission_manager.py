from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PermissionLevel(Enum):
    READ = "read"
    ACTION = "action"
    DESTRUCTIVE = "destructive"
    BLOCKED = "blocked"


@dataclass
class PermissionDecision:
    level: PermissionLevel
    allowed: bool
    requires_confirmation: bool
    reason: str


class PermissionManager:
    """
    Central permission system for AURA-1.

    READ
        Information only. No confirmation required.

    ACTION
        Safe local action. No confirmation required.

    DESTRUCTIVE
        Action capable of changing or closing something.
        Explicit confirmation required.

    BLOCKED
        AURA is not allowed to execute the action.
    """

    PERMISSIONS = {
        # ----------------------------------------------
        # SYSTEM
        # ----------------------------------------------

        ("system_info", "info"): PermissionLevel.READ,
        ("disk_info", "info"): PermissionLevel.READ,

        # ----------------------------------------------
        # APPLICATIONS
        # ----------------------------------------------

        ("app_launcher", "open"): PermissionLevel.ACTION,

        # ----------------------------------------------
        # PROCESSES
        # ----------------------------------------------

        ("process_manager", "list"): PermissionLevel.READ,
        ("process_manager", "is_running"): PermissionLevel.READ,
        ("process_manager", "close"): PermissionLevel.DESTRUCTIVE,

        # ----------------------------------------------
        # FILES
        # ----------------------------------------------

        ("file_manager", "create_folder"): PermissionLevel.ACTION,

        # Future operations
        ("file_manager", "delete_file"): PermissionLevel.DESTRUCTIVE,
        ("file_manager", "delete_folder"): PermissionLevel.DESTRUCTIVE,

        # ----------------------------------------------
        # NEVER ALLOW DIRECTLY
        # ----------------------------------------------

        ("system", "shutdown"): PermissionLevel.DESTRUCTIVE,
        ("system", "restart"): PermissionLevel.DESTRUCTIVE,

        ("shell", "execute"): PermissionLevel.BLOCKED,
        ("powershell", "execute"): PermissionLevel.BLOCKED,
        ("cmd", "execute"): PermissionLevel.BLOCKED,
    }

    def check(
        self,
        tool: str,
        action: str,
    ) -> PermissionDecision:

        level = self.PERMISSIONS.get(
            (tool, action),
            PermissionLevel.BLOCKED,
        )

        if level == PermissionLevel.READ:
            return PermissionDecision(
                level=level,
                allowed=True,
                requires_confirmation=False,
                reason="Operação apenas de leitura.",
            )

        if level == PermissionLevel.ACTION:
            return PermissionDecision(
                level=level,
                allowed=True,
                requires_confirmation=False,
                reason="Ação local considerada segura.",
            )

        if level == PermissionLevel.DESTRUCTIVE:
            return PermissionDecision(
                level=level,
                allowed=True,
                requires_confirmation=True,
                reason=(
                    "Esta ação pode alterar, fechar "
                    "ou interromper algo."
                ),
            )

        return PermissionDecision(
            level=PermissionLevel.BLOCKED,
            allowed=False,
            requires_confirmation=False,
            reason=(
                "Esta ação não está autorizada "
                "pelo sistema de permissões do AURA."
            ),
        )

    def describe(
        self,
        tool: str,
        action: str,
    ) -> dict:

        decision = self.check(
            tool,
            action,
        )

        return {
            "tool": tool,
            "action": action,
            "level": decision.level.value,
            "allowed": decision.allowed,
            "requires_confirmation": (
                decision.requires_confirmation
            ),
            "reason": decision.reason,
        }
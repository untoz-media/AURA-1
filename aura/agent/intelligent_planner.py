from __future__ import annotations

import json
import re
from typing import Any

from aura.agent.plan_executor import PlanAction
from aura.agent.planner import Plan


class IntelligentPlanner:
    """
    Converts natural-language requests into structured plans.

    IMPORTANT:
    The model only proposes actions.

    It never executes tools directly.
    """

    MAX_ACTIONS = 8

    ALLOWED_ACTIONS = {
        ("disk_info", "info"),
        ("system_info", "info"),
        ("app_launcher", "open"),
        ("process_manager", "list"),
        ("process_manager", "is_running"),
        ("process_manager", "close"),
        ("file_manager", "create_folder"),
    }

    def __init__(self, assistant):
        self.assistant = assistant

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    def create_plan(
        self,
        request: str,
    ) -> Plan | None:

        prompt = self._build_prompt(
            request
        )

        response = self.assistant.chat(
            prompt
        )

        data = self._extract_json(
            response
        )

        if data is None:
            return None

        return self._build_plan(
            request,
            data,
        )

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    def _build_prompt(
        self,
        request: str,
    ) -> str:

        return f"""
You are the planning component of AURA-1.

Your ONLY job is to convert a user request into a
small structured plan using the allowed actions below.

You DO NOT execute anything.
You DO NOT write PowerShell.
You DO NOT write shell commands.
You DO NOT write Python.
You DO NOT invent tools.

ALLOWED ACTIONS:

1. disk_info.info
Arguments:
{{}}

2. system_info.info
Arguments:
{{}}

3. app_launcher.open
Arguments:
{{"target": "application or known folder"}}

4. process_manager.list
Arguments:
{{"limit": 10}}

5. process_manager.is_running
Arguments:
{{"target": "process name"}}

6. process_manager.close
Arguments:
{{"target": "process name"}}

7. file_manager.create_folder
Arguments:
{{"path": "absolute Windows path"}}

Return ONLY valid JSON.

Do not use Markdown.
Do not use ```json.
Do not explain your answer.

Schema:

{{
  "should_plan": true,
  "description": "Short description",
  "actions": [
    {{
      "tool": "tool_name",
      "action": "action_name",
      "arguments": {{}},
      "description": "What this step does"
    }}
  ]
}}

If the request is just a normal question or conversation
and does not require actions on the computer, return:

{{
  "should_plan": false,
  "description": "",
  "actions": []
}}

Maximum actions: {self.MAX_ACTIONS}.

USER REQUEST:

{request}
""".strip()

    # --------------------------------------------------
    # JSON EXTRACTION
    # --------------------------------------------------

    @staticmethod
    def _extract_json(
        response: str,
    ) -> dict[str, Any] | None:

        text = response.strip()

        # Remove Markdown fences if the model ignores
        # the instruction.
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        try:
            data = json.loads(
                text
            )

            if isinstance(
                data,
                dict,
            ):
                return data

        except json.JSONDecodeError:
            pass

        # Try to recover the first JSON object.
        start = text.find("{")
        end = text.rfind("}")

        if (
            start == -1
            or end == -1
            or end <= start
        ):
            return None

        candidate = text[
            start : end + 1
        ]

        try:
            data = json.loads(
                candidate
            )

            if isinstance(
                data,
                dict,
            ):
                return data

        except json.JSONDecodeError:
            return None

        return None

    # --------------------------------------------------
    # PLAN BUILDING + VALIDATION
    # --------------------------------------------------

    def _build_plan(
        self,
        request: str,
        data: dict[str, Any],
    ) -> Plan | None:

        if (
            data.get("should_plan")
            is not True
        ):
            return None

        raw_actions = data.get(
            "actions"
        )

        if not isinstance(
            raw_actions,
            list,
        ):
            return None

        if not raw_actions:
            return None

        if (
            len(raw_actions)
            > self.MAX_ACTIONS
        ):
            return None

        actions: list[PlanAction] = []

        for raw_action in raw_actions:

            if not isinstance(
                raw_action,
                dict,
            ):
                return None

            tool = raw_action.get(
                "tool"
            )

            action = raw_action.get(
                "action"
            )

            if not isinstance(
                tool,
                str,
            ):
                return None

            if not isinstance(
                action,
                str,
            ):
                return None

            signature = (
                tool,
                action,
            )

            if (
                signature
                not in self.ALLOWED_ACTIONS
            ):
                return None

            arguments = raw_action.get(
                "arguments",
                {},
            )

            if not isinstance(
                arguments,
                dict,
            ):
                return None

            if not self._validate_arguments(
                tool,
                action,
                arguments,
            ):
                return None

            description = raw_action.get(
                "description",
                f"{tool}.{action}",
            )

            if not isinstance(
                description,
                str,
            ):
                description = (
                    f"{tool}.{action}"
                )

            actions.append(
                PlanAction(
                    tool=tool,
                    action=action,
                    arguments=arguments,
                    description=description,
                )
            )

        description = data.get(
            "description",
            "Plano AURA",
        )

        if not isinstance(
            description,
            str,
        ):
            description = "Plano AURA"

        return Plan(
            request=request,
            actions=actions,
            description=description,
        )

    # --------------------------------------------------
    # ARGUMENT VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate_arguments(
        tool: str,
        action: str,
        arguments: dict[str, Any],
    ) -> bool:

        # No arguments required.
        if (
            tool == "disk_info"
            and action == "info"
        ):
            return True

        if (
            tool == "system_info"
            and action == "info"
        ):
            return True

        # App launcher.
        if (
            tool == "app_launcher"
            and action == "open"
        ):
            target = arguments.get(
                "target"
            )

            return (
                isinstance(target, str)
                and bool(target.strip())
            )

        # Process list.
        if (
            tool == "process_manager"
            and action == "list"
        ):
            limit = arguments.get(
                "limit",
                10,
            )

            return (
                isinstance(limit, int)
                and 1 <= limit <= 50
            )

        # Process operations.
        if (
            tool == "process_manager"
            and action
            in {
                "is_running",
                "close",
            }
        ):
            target = arguments.get(
                "target"
            )

            return (
                isinstance(target, str)
                and bool(target.strip())
            )

        # Folder creation.
        if (
            tool == "file_manager"
            and action == "create_folder"
        ):
            path = arguments.get(
                "path"
            )

            if not isinstance(
                path,
                str,
            ):
                return False

            path = path.strip()

            # Require an absolute Windows path.
            if not re.match(
                r"^[A-Za-z]:[\\/]",
                path,
            ):
                return False

            return True

        return False
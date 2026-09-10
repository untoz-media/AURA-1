from __future__ import annotations

import json
import re
from typing import Any

from aura.agent.plan_executor import PlanAction
from aura.agent.planner import Plan


class IntelligentPlanner:
    """Convert natural-language computer requests into safe structured plans.

    The model is only allowed to *propose* actions. Every proposed action is
    validated here and is later executed through AURA's PermissionManager.
    Planning is isolated from the normal conversation memory.
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

    ACTION_HINTS = {
        "abre",
        "abrir",
        "inicia",
        "iniciar",
        "lança",
        "lanca",
        "launch",
        "open",
        "fecha",
        "fechar",
        "close",
        "cria",
        "criar",
        "create",
        "prepara",
        "preparar",
        "prepare",
        "verifica",
        "verificar",
        "check",
        "lista",
        "listar",
        "list",
    }

    COMPUTER_HINTS = {
        "app",
        "aplicação",
        "aplicacao",
        "programa",
        "processo",
        "processos",
        "pasta",
        "pastas",
        "computador",
        "pc",
        "windows",
        "sistema",
        "disco",
        "armazenamento",
        "espaço",
        "espaco",
        "obs",
        "brave",
        "notion",
        "after effects",
        "illustrator",
        "downloads",
    }

    STATE_HINTS = {
        "está aberto",
        "esta aberto",
        "está a correr",
        "esta a correr",
        "em execução",
        "em execucao",
        "espaço livre",
        "espaco livre",
        "quanto espaço",
        "quanto espaco",
    }

    def __init__(self, assistant):
        self.assistant = assistant

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    def should_attempt(self, request: str) -> bool:
        """Cheaply decide whether the local model should be used as a planner.

        Clear single-tool requests are expected to be handled by ToolRouter
        before this planner is reached. This gate mainly prevents a second
        local-model inference for ordinary conversation.
        """

        text = request.strip().lower()
        if not text:
            return False

        if any(hint in text for hint in self.STATE_HINTS):
            return True

        has_action = any(
            re.search(rf"\b{re.escape(hint)}\b", text)
            for hint in self.ACTION_HINTS
        )
        has_computer_target = any(
            hint in text
            for hint in self.COMPUTER_HINTS
        )

        return has_action and has_computer_target

    def create_plan(
        self,
        request: str,
    ) -> Plan | None:
        if not self.should_attempt(request):
            return None

        prompt = self._build_prompt(request)

        # IMPORTANT: do not use assistant.chat() here. chat() writes both the
        # planner prompt and its response into normal conversation memory and
        # can also route tools. Planning must be an isolated model inference.
        response = self.assistant.runtime.generate(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

        data = self._extract_json(response)
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

Your ONLY job is to convert the user's computer-action request into a small
structured plan using only the allowed actions below.

You DO NOT execute anything.
You DO NOT answer the user.
You DO NOT write PowerShell, shell, CMD, Python, URLs, or code.
You DO NOT invent tools or arguments.
You MUST use only the exact argument names shown below.

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

Return ONLY valid JSON. No Markdown and no explanation.

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

If the request is not a computer action, cannot be completed with the exact
allowed actions, or would require guessing a required path or target, return:

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

        # Tolerate Markdown fences if the model ignores the output rule.
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
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        # Recover one JSON object surrounded by harmless model prose.
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

        return data if isinstance(data, dict) else None

    # --------------------------------------------------
    # PLAN BUILDING + VALIDATION
    # --------------------------------------------------

    def _build_plan(
        self,
        request: str,
        data: dict[str, Any],
    ) -> Plan | None:
        if data.get("should_plan") is not True:
            return None

        raw_actions = data.get("actions")
        if not isinstance(raw_actions, list):
            return None
        if not raw_actions or len(raw_actions) > self.MAX_ACTIONS:
            return None

        actions: list[PlanAction] = []

        for raw_action in raw_actions:
            if not isinstance(raw_action, dict):
                return None

            tool = raw_action.get("tool")
            action = raw_action.get("action")
            if not isinstance(tool, str) or not isinstance(action, str):
                return None

            if (tool, action) not in self.ALLOWED_ACTIONS:
                return None

            arguments = raw_action.get("arguments", {})
            if not isinstance(arguments, dict):
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
            if not isinstance(description, str) or not description.strip():
                description = f"{tool}.{action}"

            actions.append(
                PlanAction(
                    tool=tool,
                    action=action,
                    arguments=arguments,
                    description=description.strip(),
                )
            )

        description = data.get(
            "description",
            "Plano AURA",
        )
        if not isinstance(description, str) or not description.strip():
            description = "Plano AURA"

        return Plan(
            request=request,
            actions=actions,
            description=description.strip(),
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
        if (
            (tool, action)
            in {
                ("disk_info", "info"),
                ("system_info", "info"),
            }
        ):
            return arguments == {}

        if tool == "app_launcher" and action == "open":
            if set(arguments) != {"target"}:
                return False
            target = arguments.get("target")
            return isinstance(target, str) and bool(target.strip())

        if tool == "process_manager" and action == "list":
            if not set(arguments).issubset({"limit"}):
                return False
            limit = arguments.get("limit", 10)
            return (
                isinstance(limit, int)
                and not isinstance(limit, bool)
                and 1 <= limit <= 50
            )

        if (
            tool == "process_manager"
            and action in {"is_running", "close"}
        ):
            if set(arguments) != {"target"}:
                return False
            target = arguments.get("target")
            return isinstance(target, str) and bool(target.strip())

        if tool == "file_manager" and action == "create_folder":
            if set(arguments) != {"path"}:
                return False
            path = arguments.get("path")
            if not isinstance(path, str):
                return False
            return bool(
                re.match(
                    r"^[A-Za-z]:[\\/]",
                    path.strip(),
                )
            )

        return False

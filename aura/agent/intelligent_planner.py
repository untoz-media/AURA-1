from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from aura.agent.plan_executor import PlanAction
from aura.agent.planner import Plan


@dataclass(frozen=True)
class PlanContextEntry:
    """Small ephemeral summary of one validated plan.

    This context exists only inside the running planner instance. It is not
    written to persistent memory or normal conversation history.
    """

    request: str
    description: str
    actions: tuple[str, ...]


class IntelligentPlanner:
    """Convert natural-language computer requests into safe structured plans.

    The local model may only *propose* actions. Every proposal is validated
    here and is later executed through AURA's PermissionManager.
    """

    MAX_ACTIONS = 8
    CONTEXT_LIMIT = 3
    MAX_REPAIR_ATTEMPTS = 1

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
        "faz",
        "fazer",
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

    FOLLOW_UP_HINTS = {
        "também",
        "tambem",
        "agora",
        "depois",
        "a seguir",
        "o mesmo",
        "a mesma coisa",
        "isso",
        "esse",
        "essa",
        "ele",
        "ela",
        "fecha-o",
        "fecha-a",
        "abre-o",
        "abre-a",
    }

    def __init__(self, assistant):
        self.assistant = assistant
        self._recent_plans: list[PlanContextEntry] = []

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    @property
    def context_size(self) -> int:
        return len(self._recent_plans)

    def clear_context(self) -> None:
        """Forget only ephemeral agent-planning context."""
        self._recent_plans.clear()

    def remember_plan(self, plan: Plan) -> None:
        """Record any already-validated plan as short-lived context."""
        self._remember_plan(plan)

    def remember_routed_action(
        self,
        request: str,
        routed: dict,
    ) -> None:
        """Capture a deterministic ToolRouter action for contextual follow-ups.

        Only known allowlisted signatures are recorded. Tool outputs are never
        stored here; context contains only the user's request and action shape.
        """

        tool = routed.get("tool")
        action = routed.get("action")
        target = routed.get("target")

        if action == "close_request":
            action = "close"

        if (tool, action) not in self.ALLOWED_ACTIONS:
            return

        if (tool, action) in {
            ("disk_info", "info"),
            ("system_info", "info"),
        }:
            arguments: dict[str, Any] = {}
        elif tool == "process_manager" and action == "list":
            arguments = {"limit": 10}
        elif tool == "file_manager" and action == "create_folder":
            if not isinstance(target, str) or not target.strip():
                return
            arguments = {"path": target}
        else:
            if not isinstance(target, str) or not target.strip():
                return
            arguments = {"target": target}

        if not self._validate_arguments(
            tool,
            action,
            arguments,
        ):
            return

        self._remember_plan(
            Plan(
                request=request,
                description="Ação resolvida pelo Tool Router.",
                actions=[
                    PlanAction(
                        tool=tool,
                        action=action,
                        arguments=arguments,
                        description=(
                            f"{tool}.{action}"
                        ),
                    )
                ],
            )
        )

    def should_attempt(self, request: str) -> bool:
        """Cheaply decide whether the local model should act as a planner.

        Clear single-tool requests are expected to be handled by ToolRouter
        before this planner is reached. The contextual branch permits direct
        follow-ups such as "fecha-o" only when a recent validated plan exists.
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
        if not has_action:
            return False

        has_computer_target = any(
            hint in text
            for hint in self.COMPUTER_HINTS
        )
        if has_computer_target:
            return True

        explicit_follow_up = any(
            hint in text
            for hint in self.FOLLOW_UP_HINTS
        )
        return bool(self._recent_plans) and explicit_follow_up

    def create_plan(
        self,
        request: str,
    ) -> Plan | None:
        if not self.should_attempt(request):
            return None

        prompt = self._build_prompt(request)

        # IMPORTANT: never use assistant.chat() here. chat() mutates ordinary
        # conversation memory and can route tools. Planning is isolated.
        response = self._generate_isolated(prompt)
        data = self._extract_json(response)

        # One narrow recovery path is allowed for malformed model output.
        # Valid-but-disallowed plans are never "repaired" into executable ones.
        if data is None and self.MAX_REPAIR_ATTEMPTS:
            repair_prompt = self._build_repair_prompt(
                request,
                response,
            )
            response = self._generate_isolated(repair_prompt)
            data = self._extract_json(response)

        if data is None:
            return None

        plan = self._build_plan(
            request,
            data,
        )
        if plan is None:
            return None

        self._remember_plan(plan)
        return plan

    # --------------------------------------------------
    # MODEL INFERENCE
    # --------------------------------------------------

    def _generate_isolated(self, prompt: str) -> str:
        return self.assistant.runtime.generate(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

    # --------------------------------------------------
    # PROMPTS
    # --------------------------------------------------

    def _build_prompt(
        self,
        request: str,
    ) -> str:
        recent_context = self._format_recent_context()

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
Arguments: {{}}

2. system_info.info
Arguments: {{}}

3. app_launcher.open
Arguments: {{"target": "application or known folder"}}

4. process_manager.list
Arguments: {{"limit": 10}}

5. process_manager.is_running
Arguments: {{"target": "process name"}}

6. process_manager.close
Arguments: {{"target": "process name"}}

7. file_manager.create_folder
Arguments: {{"path": "absolute Windows path"}}

RECENT VALIDATED PLAN CONTEXT:
{recent_context}

Context rules:
- Context is ephemeral and may describe a plan that did not fully complete.
- Use it only to resolve an explicit direct follow-up such as "fecha-o",
  "abre também X", or "faz o mesmo".
- Never infer a missing target from context unless the wording clearly refers
  to the most recent relevant target.
- Destructive actions still require user confirmation later; do not bypass it.

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

    def _build_repair_prompt(
        self,
        request: str,
        malformed_response: str,
    ) -> str:
        """Ask once for syntax-only JSON recovery after malformed output."""
        return f"""
You are the JSON repair component of AURA-1.

The planner response below was not valid JSON. Repair formatting only.
Do not add capabilities, tools, actions, targets, paths, or arguments that were
not already present in the response or clearly present in the user request.
If a safe repair is not possible, return exactly:
{{"should_plan": false, "description": "", "actions": []}}

Allowed action signatures:
- disk_info.info
- system_info.info
- app_launcher.open
- process_manager.list
- process_manager.is_running
- process_manager.close
- file_manager.create_folder

Return ONLY one valid JSON object and nothing else.

USER REQUEST:
{request}

MALFORMED PLANNER RESPONSE:
<planner_response>
{malformed_response}
</planner_response>
""".strip()

    # --------------------------------------------------
    # EPHEMERAL CONTEXT
    # --------------------------------------------------

    def _remember_plan(self, plan: Plan) -> None:
        actions = tuple(
            self._summarize_action(action)
            for action in plan.actions
        )
        self._recent_plans.append(
            PlanContextEntry(
                request=plan.request,
                description=plan.description,
                actions=actions,
            )
        )
        if len(self._recent_plans) > self.CONTEXT_LIMIT:
            del self._recent_plans[: -self.CONTEXT_LIMIT]

    def _format_recent_context(self) -> str:
        if not self._recent_plans:
            return "(none)"

        lines: list[str] = []
        for index, entry in enumerate(
            self._recent_plans,
            start=1,
        ):
            lines.append(
                f"{index}. Request: {entry.request}\n"
                f"   Plan: {entry.description}\n"
                f"   Actions: {'; '.join(entry.actions)}"
            )
        return "\n".join(lines)

    @staticmethod
    def _summarize_action(action: PlanAction) -> str:
        if not action.arguments:
            return f"{action.tool}.{action.action}()"
        arguments = ", ".join(
            f"{key}={value!r}"
            for key, value in sorted(action.arguments.items())
        )
        return f"{action.tool}.{action.action}({arguments})"

    # --------------------------------------------------
    # JSON EXTRACTION
    # --------------------------------------------------

    @staticmethod
    def _extract_json(
        response: str,
    ) -> dict[str, Any] | None:
        text = response.strip()

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

        if not set(data).issubset(
            {"should_plan", "description", "actions"}
        ):
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

            if not set(raw_action).issubset(
                {"tool", "action", "arguments", "description"}
            ):
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

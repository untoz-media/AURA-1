"""Start the AURA-1 local assistant."""

import sys

from aura.agent.intelligent_planner import IntelligentPlanner
from aura.agent.plan_executor import PlanExecutor
from aura.agent.planner import Planner
from aura.agent.recovery_planner import RecoveryPlanner
from aura.agent.tool_router import ToolRouter
from aura.core.assistant import AuraAssistant
from aura.profiles import PROFILE_LABELS
from aura.ui.console import AuraConsole


CATEGORY_LABELS = {
    "general": "Geral",
    "profile": "Perfil",
    "preference": "Preferência",
    "project": "Projeto",
    "fact": "Facto",
}


def parse_remember_payload(payload: str):
    parts = [part.strip() for part in payload.split("|")]
    if not parts or not parts[0]:
        return None

    first = parts[0].split(maxsplit=1)
    if len(first) != 2:
        return None

    key, value = first
    category = "general"
    importance = 3

    if len(parts) >= 2 and parts[1]:
        category = parts[1].lower()

    if len(parts) >= 3 and parts[2]:
        try:
            importance = int(parts[2])
        except ValueError:
            return None

    if len(parts) > 3:
        return None

    return key, value, category, importance


def parse_setting_value(raw: str, current):
    if isinstance(current, bool):
        value = raw.lower()
        if value in {"true", "on", "1", "sim", "yes"}:
            return True
        if value in {"false", "off", "0", "não", "nao", "no"}:
            return False
        return None

    if isinstance(current, int) and not isinstance(current, bool):
        try:
            return int(raw)
        except ValueError:
            return None

    if isinstance(current, float):
        try:
            return float(raw)
        except ValueError:
            return None

    return raw


def parse_tool_command(payload: str):
    """Parse the legacy explicit /tool payload used by compatibility tests."""
    parts = payload.split(maxsplit=2)
    if parts == ["system_info"]:
        return "system_info", "", ""
    if len(parts) < 2:
        return None

    tool_name = parts[0]
    action = parts[1]
    extra = parts[2].strip() if len(parts) == 3 else ""
    return tool_name, action, extra


def execute_cli_tool(assistant, tool_name: str, action: str, extra: str):
    """Execute one explicitly selected legacy CLI tool through its registry."""
    if tool_name == "system_info" and not action and not extra:
        return assistant.execute_tool(tool_name)

    if tool_name == "files":
        path = extra or "."
        if len(path) >= 2 and path[0] == path[-1] and path[0] in "\"'":
            path = path[1:-1]
        return assistant.execute_tool(tool_name, action=action, path=path)

    if tool_name == "calculator":
        expression = action if not extra else f"{action} {extra}"
        return assistant.execute_tool(tool_name, expression=expression)

    if tool_name == "datetime":
        timezone = extra or "Europe/Lisbon"
        return assistant.execute_tool(tool_name, action=action, timezone=timezone)

    return assistant.execute_tool(tool_name, action=action)


def format_tool_response(tool_name: str, result: dict) -> str:
    if not result.get("sucesso", True):
        return "Não consegui executar essa ação: " + result.get(
            "erro",
            "erro desconhecido",
        )

    if tool_name == "disk_info":
        return (
            f"Tens {result.get('livre_gb', '?')} GB livres "
            f"de {result.get('total_gb', '?')} GB. "
            f"O disco está {result.get('percentagem_usada', '?')}% ocupado."
        )

    if tool_name == "system_info":
        return (
            f"Estás a usar {result.get('sistema_operativo', 'desconhecido')} "
            f"{result.get('versao_sistema', '')}, com "
            f"{result.get('cpu_logical', '?')} processadores lógicos."
        )

    if tool_name == "app_launcher":
        action = result.get("acao")
        if action == "abrir_pasta":
            return f"Abri a pasta {result.get('target', '')}."
        if action in {"abrir_app", "abrir_app_descoberta"}:
            name = result.get("nome") or result.get("target") or "a aplicação"
            return f"Abri {name}."

    if tool_name == "file_manager" and result.get("acao") == "criar_pasta":
        return f"Criei a pasta em {result.get('path')}."

    if tool_name == "process_manager":
        if result.get("acao") == "fechar_processo":
            processes = result.get("processos", [])
            names = sorted(
                {process.get("nome", "processo") for process in processes}
            )
            return "Fechei: " + ", ".join(names) + "."

        if "em_execucao" in result:
            if result.get("em_execucao"):
                processes = result.get("processos", [])
                if processes:
                    return f"Sim. {processes[0].get('nome')} está em execução."
                return "Sim, está em execução."
            return "Não, não está em execução."

        if "processos" in result:
            processes = result.get("processos", [])
            if not processes:
                return "Não encontrei processos em execução."

            lines = [
                f"{process.get('nome', 'Desconhecido')} — "
                f"{process.get('memoria_mb', '?')} MB"
                for process in processes[:10]
            ]
            return "Processos com maior utilização de memória:\n\n" + "\n".join(
                f"• {line}" for line in lines
            )

    return str(result)


def print_memory(assistant: AuraAssistant, ui: AuraConsole) -> None:
    memories = assistant.persistent_memory.data
    if not memories:
        ui.info("Não existem memórias persistentes.")
        return

    for key, entry in memories.items():
        ui.info(
            f"{key} = {entry.value} "
            f"[{entry.category}, {entry.importance}/5]"
        )


def show_help(ui: AuraConsole) -> None:
    ui.aura(
        "Comandos disponíveis:\n\n"
        "/help\n"
        "/info\n"
        "/clear\n"
        "/memory\n"
        "/memory-search TEXTO\n"
        "/remember CHAVE VALOR\n"
        "/forget CHAVE\n"
        "/clear-memory\n"
        "/profiles\n"
        "/profile fast|balanced|deep\n"
        "/settings\n"
        "/set CHAVE VALOR\n"
        "/reset-settings\n"
        "/tools\n"
        "/exit\n\n"
        "Também podes falar comigo normalmente e pedir ações no Windows."
    )


def render_plan_results(results, ui: AuraConsole) -> None:
    """Render completed steps and warnings from one plan pass."""
    for action_result in results:
        if action_result.success:
            if action_result.result:
                ui.success(
                    format_tool_response(
                        action_result.tool,
                        action_result.result,
                    )
                )
            continue

        detail = action_result.message or "A ação não foi concluída."
        ui.warning(
            f"{action_result.tool}.{action_result.action}: {detail}"
        )


def _execute_plan_once(
    plan,
    plan_executor: PlanExecutor,
    ui: AuraConsole,
):
    """Execute one plan pass, including protected-action confirmations."""

    valid, reason = Planner().validate(plan)
    if not valid:
        ui.error(f"Plano inválido: {reason}")
        return None, False

    ui.plan(plan.description, plan.actions)
    result = plan_executor.execute(plan.actions)

    while result.status == "confirmation_required":
        if result.pending_action is None or result.pending_index is None:
            ui.error("O plano pediu confirmação sem indicar a ação pendente.")
            return None, False

        action = result.pending_action
        description = action.description or f"{action.tool}.{action.action}"
        confirmed = ui.confirm(
            "AURA precisa de autorização para continuar o plano:\n\n"
            f"{description}"
        )

        if not confirmed:
            return result, True

        result = plan_executor.execute_confirmed(
            plan.actions,
            result.pending_index,
            previous_results=result.results,
        )

    return result, False


def execute_agent_plan(
    plan,
    plan_executor: PlanExecutor,
    ui: AuraConsole,
    recovery_planner: RecoveryPlanner | None = None,
) -> None:
    """Execute a plan and permit at most one result-aware recovery pass."""

    result, cancelled = _execute_plan_once(
        plan,
        plan_executor,
        ui,
    )
    if result is None:
        return

    render_plan_results(result.results, ui)

    if cancelled:
        ui.warning("Plano cancelado antes da ação protegida.")
        return

    if result.status == "completed":
        ui.plan_complete(result.completed, result.total)
        return

    # v1.3: one bounded recovery pass. We deliberately never recurse into
    # execute_agent_plan(), so a failed recovery cannot create another recovery.
    if (
        recovery_planner is not None
        and recovery_planner.should_recover(plan, result)
    ):
        ui.warning(
            "Uma ou mais etapas falharam. "
            "AURA vai analisar uma recuperação segura."
        )

        try:
            with ui.loading("AURA está a analisar o resultado..."):
                recovery_plan = recovery_planner.create_recovery_plan(
                    plan,
                    result,
                )
        except Exception as exc:
            ui.warning(f"Recovery Planner indisponível: {exc}")
            recovery_plan = None

        if recovery_plan is not None:
            ui.info("AURA encontrou uma tentativa de recuperação segura.")
            recovery_result, recovery_cancelled = _execute_plan_once(
                recovery_plan,
                plan_executor,
                ui,
            )

            if recovery_result is None:
                return

            render_plan_results(recovery_result.results, ui)

            if recovery_cancelled:
                ui.warning("Recuperação cancelada antes de uma ação protegida.")
                return

            if recovery_result.status == "completed":
                ui.success("Recuperação concluída. O AURA não precisou de novo ciclo.")
                return

            if recovery_result.status == "blocked":
                ui.blocked(
                    "A tentativa de recuperação foi bloqueada pelo sistema "
                    "de permissões."
                )
                return

            ui.warning(
                "A tentativa de recuperação não resolveu tudo. "
                "Por segurança, o AURA não vai tentar novamente automaticamente."
            )
            return

        ui.warning(
            "Não encontrei uma recuperação automática segura. "
            "O AURA não vai inventar uma alternativa."
        )

    if result.status == "completed_with_warnings":
        ui.plan_complete(result.completed, result.total)
        ui.warning(
            "Plano concluído com avisos: algumas etapas falharam, "
            "mas as ações independentes continuaram."
        )
        return

    if result.status == "blocked":
        ui.blocked(
            "Uma ação do plano foi bloqueada pelo sistema de permissões."
        )
        return

    ui.error(f"O plano terminou com estado: {result.status}")


def handle_tool_router_result(
    routed: dict,
    tool_router: ToolRouter,
    ui: AuraConsole,
) -> bool:
    """Render/confirm one ToolRouter result. Return True when handled."""
    if routed.get("requires_confirmation"):
        target = routed.get("target", "")
        confirmed = ui.confirm(
            "AURA pretende executar uma ação protegida:\n\n"
            f"Fechar '{target}'"
        )
        if not confirmed:
            ui.warning("Ação cancelada.")
            return True

        result = tool_router.execute_confirmed_action(
            "process_manager",
            "close",
            target,
        )
        ui.aura(format_tool_response("process_manager", result))
        return True

    result = routed.get("result")
    if result is None:
        ui.error("A ferramenta não devolveu resultado.")
        return True

    if (
        routed["tool"] == "process_manager"
        and "processos" in result
        and "em_execucao" not in result
    ):
        ui.processes(result.get("processos", []))
        return True

    ui.aura(format_tool_response(routed["tool"], result))
    return True


def main() -> None:
    ui = AuraConsole()
    ui.header()
    ui.info("A iniciar o Agent Runtime...")

    # Fast deterministic components do not require model inference.
    tool_router = ToolRouter()
    planner = Planner()
    plan_executor = PlanExecutor()

    try:
        with ui.loading("A carregar inteligência local..."):
            assistant = AuraAssistant()
    except Exception as exc:
        ui.error(f"Não foi possível iniciar o modelo: {exc}")
        return

    intelligent_planner = IntelligentPlanner(assistant)
    recovery_planner = RecoveryPlanner(intelligent_planner)

    ui.success("AURA-1 está operacional.")
    ui.info("Alpha 2 Development • Intelligent Agent Runtime v1.3 Online")

    while True:
        try:
            message = ui.ask()
        except (EOFError, KeyboardInterrupt):
            ui.aura("Até já!")
            break

        if not message:
            continue

        command = message.lower().strip()

        if command in {"/exit", "/quit", "exit", "quit", "sair"}:
            ui.aura("Até já!")
            break

        if command == "/help":
            show_help(ui)
            continue

        if command == "/info":
            ui.aura(
                "AURA-1 Alpha 2\n\n"
                f"Modelo: {assistant.config.model_name}\n"
                f"Perfil: {assistant.settings.active_profile}\n"
                f"Memória da conversa: {len(assistant.memory.messages)} mensagens\n"
                f"Memórias persistentes: {len(assistant.persistent_memory.data)}\n"
                f"Contexto efémero do Planner: {intelligent_planner.context_size}/3\n"
                "Agent Runtime: online\n"
                "Tool Router v2: online\n"
                "Deterministic Planner: online\n"
                "Intelligent Planner v1.3: online\n"
                "State Observer: online\n"
                "Result-aware Recovery: online\n"
                "Permission Manager: online"
            )
            continue

        if command == "/clear":
            assistant.clear_memory()
            intelligent_planner.clear_context()
            ui.success("Conversa e contexto efémero do Planner limpos.")
            continue

        if command == "/memory":
            print_memory(assistant, ui)
            continue

        if command.startswith("/memory-search "):
            query = message[len("/memory-search ") :].strip()
            matches = assistant.search_memory(query)
            if not matches:
                ui.info(f"Não encontrei memórias para '{query}'.")
            else:
                for key, entry in matches.items():
                    ui.info(f"{key} = {entry.value}")
            continue

        if command.startswith("/remember "):
            payload = message[len("/remember ") :].strip()
            parsed = parse_remember_payload(payload)
            if parsed is None:
                ui.error("Formato inválido para /remember.")
                continue

            key, value, category, importance = parsed
            try:
                assistant.remember(key, value, category, importance)
                ui.success(f"Memória guardada: {key} = {value}")
            except ValueError as exc:
                ui.error(str(exc))
            continue

        if command.startswith("/forget "):
            key = message[len("/forget ") :].strip()
            if assistant.forget(key):
                ui.success(f"Memória '{key}' apagada.")
            else:
                ui.warning(f"Não encontrei '{key}'.")
            continue

        if command == "/clear-memory":
            assistant.clear_persistent_memory()
            ui.success("Todas as memórias persistentes foram apagadas.")
            continue

        if command == "/profiles":
            current = assistant.settings.active_profile
            ui.aura(
                "Perfis disponíveis:\n\n"
                f"fast{' ← atual' if current == 'fast' else ''}\n"
                f"balanced{' ← atual' if current == 'balanced' else ''}\n"
                f"deep{' ← atual' if current == 'deep' else ''}"
            )
            continue

        if command.startswith("/profile "):
            profile = message[len("/profile ") :].strip().lower()
            if profile not in PROFILE_LABELS:
                ui.error("Perfil inválido.")
                continue

            if assistant.settings.set_profile(profile):
                ui.success(f"Perfil alterado para {profile}.")
                ui.info("Reinicia o AURA para aplicar totalmente.")
            continue

        if command == "/settings":
            for key, value in assistant.settings.data.items():
                if key != "system_prompt":
                    ui.info(f"{key} = {value}")
            continue

        if command.startswith("/set "):
            payload = message[len("/set ") :].strip()
            parts = payload.split(maxsplit=1)
            if len(parts) != 2:
                ui.error("Usa /set CHAVE VALOR")
                continue

            key, raw_value = parts
            current = assistant.settings.get(key)
            if current is None:
                ui.error("Definição desconhecida.")
                continue

            value = parse_setting_value(raw_value, current)
            if value is None:
                ui.error("Valor inválido.")
                continue

            if key == "system_prompt":
                ui.blocked("system_prompt é gerido internamente.")
                continue

            if assistant.settings.set(key, value):
                ui.success(f"{key} = {value}")
            continue

        if command == "/reset-settings":
            assistant.settings.reset()
            ui.success("Definições repostas.")
            continue

        if command == "/tools":
            ui.aura(
                "AURA Tools\n\n"
                "• System Info\n"
                "• Disk Info\n"
                "• App Launcher\n"
                "• App Discovery\n"
                "• File Manager\n"
                "• Process Manager\n"
                "• Tool Router v2\n"
                "• Deterministic Planner\n"
                "• Intelligent Planner v1.3\n"
                "• State Observer\n"
                "• Contextual Follow-ups\n"
                "• Result-aware Recovery\n"
                "• Resilient Plan Executor\n"
                "• Action Executor\n"
                "• Permission Manager"
            )
            continue

        # 1. Fast deterministic multi-step routines.
        try:
            plan = planner.create_plan(message)
        except Exception as exc:
            ui.error(f"Erro no Planner: {exc}")
            continue

        if plan is not None:
            intelligent_planner.remember_plan(plan)
            execute_agent_plan(
                plan,
                plan_executor,
                ui,
                recovery_planner,
            )
            continue

        # 2. Fast deterministic single-tool requests.
        try:
            routed = tool_router.route(message)
        except Exception as exc:
            ui.error(f"Erro no Tool Router: {exc}")
            continue

        if routed is not None:
            intelligent_planner.remember_routed_action(message, routed)
            handle_tool_router_result(routed, tool_router, ui)
            continue

        # 3. Flexible model-generated plans. This is deliberately after the
        # deterministic paths so simple commands stay fast on local hardware.
        if intelligent_planner.should_attempt(message):
            try:
                with ui.loading("AURA está a criar um plano..."):
                    plan = intelligent_planner.create_plan(message)
            except Exception as exc:
                ui.warning(f"Intelligent Planner indisponível: {exc}")
                plan = None

            if plan is not None:
                execute_agent_plan(
                    plan,
                    plan_executor,
                    ui,
                    recovery_planner,
                )
                continue

        # 4. Normal local conversation.
        try:
            with ui.loading("AURA está a pensar..."):
                response = assistant.chat(message)
        except Exception as exc:
            ui.error(f"Erro do modelo: {exc}")
            continue

        ui.aura(response)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(
                encoding="utf-8",
                errors="backslashreplace",
            )

    main()

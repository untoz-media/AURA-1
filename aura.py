"""Start the AURA-1 local assistant."""

from aura.core.assistant import AuraAssistant
from aura.profiles import PROFILE_LABELS


CATEGORY_LABELS = {
    "general": "Geral",
    "profile": "Perfil",
    "preference": "Preferência",
    "project": "Projeto",
    "fact": "Facto",
}


def print_help() -> None:
    """Show the commands available in the AURA-1 CLI."""
    print(
        "\nComandos AURA-1:\n"
        "  /help                         — mostrar esta ajuda\n"
        "  /clear                        — limpar a memória da conversa atual\n"
        "  /remember K V                 — guardar uma memória persistente\n"
        "  /remember K V | CATEGORIA | N — guardar memória com categoria e importância\n"
        "  /memory                       — mostrar as memórias persistentes\n"
        "  /memory-search TEXTO         — pesquisar nas memórias persistentes\n"
        "  /forget K                    — apagar uma memória persistente\n"
        "  /clear-memory                — apagar todas as memórias persistentes\n"
        "  /tools                       — mostrar as tools disponíveis\n"
        "  /tool calculator EXPRESSÃO   — executar a calculadora\n"
        "  /tool datetime AÇÃO [FUSO]   — consultar data/hora\n"
        "  /settings                    — mostrar as definições atuais\n"
        "  /set K V                     — alterar uma definição\n"
        "  /reset-settings              — repor as definições de origem\n"
        "  /profiles                    — mostrar os perfis disponíveis\n"
        "  /profile NOME                — selecionar um perfil\n"
        "  /info                        — mostrar o estado atual do AURA-1\n"
        "  /exit                        — terminar o AURA-1\n"
    )


def print_info(assistant: AuraAssistant) -> None:
    """Show the current runtime configuration."""
    config = assistant.config
    profile = assistant.settings.active_profile
    print(
        "\nAURA-1 — Informação\n"
        f"Modelo: {config.model_name}\n"
        f"Idioma: {config.language}\n"
        f"Perfil: {profile}\n"
        f"Memória de conversa: ativa ({len(assistant.memory.messages)} mensagens)\n"
        f"Memórias persistentes: {len(assistant.persistent_memory.data)}\n"
        f"Tools disponíveis: {len(assistant.list_tools())}\n"
        f"Contexto máximo: {config.max_history_messages} mensagens\n"
        f"Pensamento: {'ativo' if config.enable_thinking else 'desativado'}\n"
        f"Máximo de tokens: {config.max_new_tokens}\n"
        f"Temperatura: {config.temperature}\n"
    )


def print_profiles(assistant: AuraAssistant) -> None:
    """Show the available runtime profiles."""
    current = assistant.settings.active_profile
    print("\nAURA-1 — Perfis")
    print(f"  {PROFILE_LABELS['fast']}     — respostas mais rápidas{' ← atual' if current == 'fast' else ''}")
    print(f"  {PROFILE_LABELS['balanced']} — equilíbrio{' ← atual' if current == 'balanced' else ''}")
    print(f"  {PROFILE_LABELS['deep']}     — respostas mais elaboradas{' ← atual' if current == 'deep' else ''}")
    print("\nUsa /profile fast, /profile balanced ou /profile deep.")


def print_settings(assistant: AuraAssistant) -> None:
    """Show user-facing settings."""
    print("\nAURA-1 — Definições")
    for key, value in assistant.settings.data.items():
        if key == "system_prompt":
            print("  system_prompt = [interno]")
        else:
            print(f"  {key} = {value}")
    print(f"  active_profile = {assistant.settings.active_profile}")
    print("\nNota: algumas definições só têm efeito ao reiniciar o AURA-1.")


def print_tools(assistant: AuraAssistant) -> None:
    """Show registered tools."""
    tools = assistant.list_tools()
    print("\nAURA-1 — Tools disponíveis")
    if not tools:
        print("  Nenhuma tool registada.")
        return
    for tool in tools:
        print(f"  {tool.name} — {tool.description}")


def parse_tool_command(payload: str):
    """Parse an explicit tool command."""
    parts = payload.split(maxsplit=2)
    if len(parts) < 2:
        return None
    tool_name = parts[0]
    action = parts[1]
    extra = parts[2].strip() if len(parts) == 3 else ""
    return tool_name, action, extra


def print_tool_result(result) -> None:
    """Print one normalized tool result."""
    if result.success:
        print(f"AURA: Resultado de {result.tool_name}: {result.output}")
    else:
        print(f"AURA: Erro na tool {result.tool_name}: {result.error}")


def execute_cli_tool(assistant: AuraAssistant, tool_name: str, action: str, extra: str):
    """Map CLI tool syntax to explicit tool arguments."""
    if tool_name == "calculator":
        expression = action if not extra else f"{action} {extra}"
        return assistant.execute_tool(tool_name, expression=expression)

    if tool_name == "datetime":
        timezone = extra or "Europe/Lisbon"
        return assistant.execute_tool(tool_name, action=action, timezone=timezone)

    return assistant.execute_tool(tool_name, action=action)


def parse_setting_value(raw: str, current):
    """Convert CLI text to the same type as the current setting."""
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


def parse_remember_payload(payload: str):
    """Parse simple or extended /remember syntax."""
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


def print_memory_entry(key: str, entry) -> None:
    """Print one structured memory entry."""
    category = CATEGORY_LABELS.get(entry.category, entry.category)
    stars = "★" * entry.importance + "☆" * (5 - entry.importance)
    print(f"  {key} = {entry.value}")
    print(f"    Categoria: {category} | Importância: {stars}")


def print_persistent_memory(assistant: AuraAssistant) -> None:
    """Show persistent memory entries grouped by category."""
    memories = assistant.persistent_memory.data
    if not memories:
        print("AURA: Não tenho memórias persistentes guardadas.")
        return

    print("\nAURA — Memória persistente")
    for category in CATEGORY_LABELS:
        entries = [(key, entry) for key, entry in memories.items() if entry.category == category]
        if not entries:
            continue
        print(f"\n[{CATEGORY_LABELS[category]}]")
        for key, entry in sorted(entries, key=lambda item: (-item[1].importance, item[0])):
            print_memory_entry(key, entry)


def print_memory_search(assistant: AuraAssistant, query: str) -> None:
    """Show matching persistent memories."""
    matches = assistant.search_memory(query)
    if not matches:
        print(f"AURA: Não encontrei memórias para '{query}'.")
        return

    print(f"\nAURA — Resultados para '{query}'")
    for key, entry in sorted(matches.items(), key=lambda item: (-item[1].importance, item[0])):
        print_memory_entry(key, entry)


def main() -> None:
    print("=" * 60)
    print("AURA-1")
    print("Untoz AI Assistant")
    print("Escreve /help para ver os comandos.")
    print("=" * 60)

    try:
        assistant = AuraAssistant()
    except Exception as exc:
        print(f"\nAURA-1: Não foi possível iniciar o modelo.\nErro: {exc}")
        return

    while True:
        try:
            message = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAURA: Até já!")
            break

        if not message:
            continue

        command = message.lower()

        if command in {"/exit", "/quit", "sair", "exit", "quit"}:
            print("AURA: Até já!")
            break

        if command == "/help":
            print_help()
            continue

        if command == "/info":
            print_info(assistant)
            continue

        if command == "/tools":
            print_tools(assistant)
            continue

        if command.startswith("/tool "):
            parsed = parse_tool_command(message[len("/tool ") :].strip())
            if parsed is None:
                print("AURA: Usa /tool calculator EXPRESSÃO ou /tool datetime AÇÃO [FUSO]")
                continue
            tool_name, action, extra = parsed
            result = execute_cli_tool(assistant, tool_name, action, extra)
            print_tool_result(result)
            continue

        if command == "/profiles":
            print_profiles(assistant)
            continue

        if command.startswith("/profile "):
            profile = message[len("/profile ") :].strip().lower()
            if profile not in PROFILE_LABELS:
                print("AURA: Perfil inválido. Usa fast, balanced ou deep.")
                continue
            if assistant.settings.set_profile(profile):
                print(f"AURA: Perfil alterado para {PROFILE_LABELS[profile]}.")
                print("AURA: Reinicia o AURA-1 para aplicar o novo perfil.")
            else:
                print("AURA: Não foi possível alterar o perfil.")
            continue

        if command == "/clear":
            assistant.clear_memory()
            print("AURA: Memória da conversa atual limpa.")
            continue

        if command == "/memory":
            print_persistent_memory(assistant)
            continue

        if command.startswith("/memory-search "):
            query = message[len("/memory-search ") :].strip()
            if not query:
                print("AURA: Usa /memory-search TEXTO")
                continue
            print_memory_search(assistant, query)
            continue

        if command == "/clear-memory":
            assistant.clear_persistent_memory()
            print("AURA: Todas as memórias persistentes foram apagadas.")
            continue

        if command == "/settings":
            print_settings(assistant)
            continue

        if command == "/reset-settings":
            assistant.settings.reset()
            print("AURA: Definições repostas. Reinicia o AURA-1 para aplicar todas as alterações.")
            continue

        if command.startswith("/set "):
            payload = message[len("/set ") :].strip()
            parts = payload.split(maxsplit=1)
            if len(parts) != 2:
                print("AURA: Usa /set CHAVE VALOR")
                continue
            key, raw_value = parts
            current = assistant.settings.get(key)
            if current is None:
                print(f"AURA: Definição desconhecida: {key}")
                continue
            value = parse_setting_value(raw_value, current)
            if value is None:
                print(f"AURA: Valor inválido para {key}.")
                continue
            if key == "system_prompt":
                print("AURA: O system_prompt é gerido internamente nesta fase.")
                continue
            if assistant.settings.set(key, value):
                print(f"AURA: Definição alterada — {key} = {value}")
                print("AURA: Reinicia o AURA-1 para aplicar a alteração.")
            else:
                print(f"AURA: Não foi possível alterar {key}.")
            continue

        if command.startswith("/remember "):
            payload = message[len("/remember ") :].strip()
            parsed = parse_remember_payload(payload)
            if parsed is None:
                print("AURA: Usa /remember CHAVE VALOR ou /remember CHAVE VALOR | CATEGORIA | IMPORTÂNCIA")
                continue
            key, value, category, importance = parsed
            try:
                assistant.remember(key, value, category, importance)
            except ValueError as exc:
                print(f"AURA: {exc}")
                continue
            print(f"AURA: Memória guardada — {key} = {value}")
            print(f"AURA: Categoria: {category} | Importância: {importance}/5")
            continue

        if command.startswith("/forget "):
            key = message[len("/forget ") :].strip()
            if not key:
                print("AURA: Usa /forget CHAVE")
                continue
            if assistant.forget(key):
                print(f"AURA: Memória '{key}' apagada.")
            else:
                print(f"AURA: Não encontrei a memória '{key}'.")
            continue

        try:
            routed_result = assistant.execute_routed_tool(message)
            if routed_result is not None:
                print_tool_result(routed_result)
                continue
            response = assistant.chat(message)
        except Exception as exc:
            print(f"AURA: Ocorreu um erro: {exc}")
            continue

        print(f"AURA: {response}")


if __name__ == "__main__":
    main()

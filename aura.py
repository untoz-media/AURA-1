"""Start the AURA-1 local assistant."""

from aura.core.assistant import AuraAssistant
from aura.profiles import PROFILE_LABELS


def print_help() -> None:
    """Show the commands available in the AURA-1 CLI."""
    print(
        "\nComandos AURA-1:\n"
        "  /help                 — mostrar esta ajuda\n"
        "  /clear                — limpar a memória da conversa atual\n"
        "  /remember K V         — guardar uma memória persistente\n"
        "  /memory               — mostrar as memórias persistentes\n"
        "  /forget K             — apagar uma memória persistente\n"
        "  /clear-memory         — apagar todas as memórias persistentes\n"
        "  /settings             — mostrar as definições atuais\n"
        "  /set K V              — alterar uma definição\n"
        "  /reset-settings       — repor as definições de origem\n"
        "  /profiles             — mostrar os perfis disponíveis\n"
        "  /profile NOME         — selecionar um perfil\n"
        "  /info                 — mostrar o estado atual do AURA-1\n"
        "  /exit                 — terminar o AURA-1\n"
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
            parts = payload.split(maxsplit=1)
            if len(parts) != 2:
                print("AURA: Usa /remember CHAVE VALOR")
                continue
            key, value = parts
            assistant.remember(key, value)
            print(f"AURA: Memória guardada — {key} = {value}")
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
            response = assistant.chat(message)
        except Exception as exc:
            print(f"AURA: Ocorreu um erro: {exc}")
            continue

        print(f"AURA: {response}")


def print_persistent_memory(assistant: AuraAssistant) -> None:
    """Show persistent memory entries."""
    memories = assistant.persistent_memory.data
    if not memories:
        print("AURA: Não tenho memórias persistentes guardadas.")
        return

    print("\nAURA — Memória persistente")
    for key, value in memories.items():
        print(f"  {key} = {value}")


if __name__ == "__main__":
    main()

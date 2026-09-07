"""Start the AURA-1 local assistant."""

from aura.core.assistant import AuraAssistant


def print_help() -> None:
    """Show the commands available in the AURA-1 CLI."""
    print(
        "\nComandos AURA-1:\n"
        "  /help           — mostrar esta ajuda\n"
        "  /clear          — limpar a memória da conversa atual\n"
        "  /remember K V   — guardar uma memória persistente\n"
        "  /memory         — mostrar as memórias persistentes\n"
        "  /forget K       — apagar uma memória persistente\n"
        "  /clear-memory   — apagar todas as memórias persistentes\n"
        "  /info           — mostrar o estado atual do AURA-1\n"
        "  /exit           — terminar o AURA-1\n"
    )


def print_info(assistant: AuraAssistant) -> None:
    """Show the current runtime configuration."""
    config = assistant.config
    print(
        "\nAURA-1 — Informação\n"
        f"Modelo: {config.model_name}\n"
        f"Idioma: {config.language}\n"
        f"Memória de conversa: ativa ({len(assistant.memory.messages)} mensagens)\n"
        f"Memórias persistentes: {len(assistant.persistent_memory.data)}\n"
        f"Contexto máximo: {config.max_history_messages} mensagens\n"
        f"Pensamento: {'ativo' if config.enable_thinking else 'desativado'}\n"
    )


def print_persistent_memory(assistant: AuraAssistant) -> None:
    """Show persistent memory entries."""
    memories = assistant.persistent_memory.data
    if not memories:
        print("AURA: Não tenho memórias persistentes guardadas.")
        return

    print("\nAURA — Memória persistente")
    for key, value in memories.items():
        print(f"  {key} = {value}")


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


if __name__ == "__main__":
    main()

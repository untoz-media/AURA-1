"""Start the AURA-1 local assistant."""

from aura.core.assistant import AuraAssistant


def print_help() -> None:
    """Show the commands available in the AURA-1 CLI."""
    print(
        "\nComandos AURA-1:\n"
        "  /help   — mostrar esta ajuda\n"
        "  /clear  — limpar a memória da conversa\n"
        "  /info   — mostrar o estado atual do AURA-1\n"
        "  /exit   — terminar o AURA-1\n"
    )


def print_info(assistant: AuraAssistant) -> None:
    """Show the current runtime configuration."""
    config = assistant.config
    print(
        "\nAURA-1 — Informação\n"
        f"Modelo: {config.model_name}\n"
        f"Idioma: {config.language}\n"
        f"Memória: ativa ({len(assistant.memory.messages)} mensagens)\n"
        f"Contexto máximo: {config.max_history_messages} mensagens\n"
        f"Pensamento: {'ativo' if config.enable_thinking else 'desativado'}\n"
    )


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
            print("AURA: Memória limpa.")
            continue

        if command == "/info":
            print_info(assistant)
            continue

        try:
            response = assistant.chat(message)
        except Exception as exc:
            print(f"AURA: Ocorreu um erro: {exc}")
            continue

        print(f"AURA: {response}")


if __name__ == "__main__":
    main()

"""Start the AURA-1 local assistant."""

from aura.core.assistant import AuraAssistant


def main() -> None:
    print("=" * 60)
    print("AURA-1")
    print("Untoz AI Assistant")
    print("Escreve 'sair' para terminar.")
    print("=" * 60)

    assistant = AuraAssistant()

    while True:
        try:
            message = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAURA: Até já!")
            break

        if message.lower() in {"sair", "exit", "quit"}:
            print("AURA: Até já!")
            break

        try:
            response = assistant.chat(message)
        except Exception as exc:
            print(f"AURA: Ocorreu um erro: {exc}")
            continue

        print(f"AURA: {response}")


if __name__ == "__main__":
    main()

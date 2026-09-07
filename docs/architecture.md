# AURA-1 Architecture

## High-level design

```text
Qwen3-4B-Base
      │
      ▼
 AURA Dataset
      │
      ▼
   QLoRA
      │
      ▼
 AURA-1-v0.1
      │
      ├── Local inference / Ollama
      │
      └── AURA assistant integration
```

## Aplicação local

```text
Navegador ── HTTP em 127.0.0.1 ── AURA Web
                                      │
                         ┌────────────┼────────────┐
                         ▼            ▼            ▼
                    Qwen local      Memória      Tools seguras
```

O servidor web usa apenas a biblioteca padrão do Python, inicia o modelo em
segundo plano e conserva uma instância da assistente por execução. Pedidos de
conversa são processados um de cada vez para proteger o runtime local. O corpo
dos pedidos e o tamanho das mensagens têm limites explícitos. Host, Origin e
binding restringem a interface ao computador local; respostas têm CSP e outros
cabeçalhos de proteção. O frontend insere texto com APIs que não interpretam
HTML gerado pelo modelo.

## Design principles

1. **Local-first** — prioritize practical local inference.
2. **Efficient** — keep the model small enough for accessible hardware.
3. **Portuguese-first quality** — specifically evaluate European Portuguese.
4. **Reproducible** — version datasets, configurations and evaluation results.
5. **Open development** — publish useful code and documentation where licensing permits.

## Separation of concerns

AURA-1 is the model. AURA is the assistant application and orchestration layer. Tool use, memory, UI, automation and external services should remain outside the model whenever practical.

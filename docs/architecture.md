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

## Design principles

1. **Local-first** — prioritize practical local inference.
2. **Efficient** — keep the model small enough for accessible hardware.
3. **Portuguese-first quality** — specifically evaluate European Portuguese.
4. **Reproducible** — version datasets, configurations and evaluation results.
5. **Open development** — publish useful code and documentation where licensing permits.

## Separation of concerns

AURA-1 is the model. AURA is the assistant application and orchestration layer. Tool use, memory, UI, automation and external services should remain outside the model whenever practical.

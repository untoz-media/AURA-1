# AURA-1

**AURA-1** is an open-source AI model project developed by **Untoz** as the language model foundation for the AURA personal AI assistant.

> **Status:** Early development — Milestone 001: Project Initialization

## Project

- **Name:** AURA-1
- **Organization:** Untoz
- **Project:** AURA
- **Model type:** Large Language Model (LLM)
- **Base model:** Qwen3-4B-Base
- **Target size:** ~4B parameters
- **Initial fine-tuning approach:** QLoRA
- **Primary language:** Portuguese (European Portuguese)
- **Secondary language:** English
- **Runtime target:** Ollama / local inference
- **Planned release:** Hugging Face

## Goals

AURA-1 is intended to be a compact, capable and efficient model that can act as the language brain of AURA. The project prioritizes local use, practical assistant capabilities, Portuguese quality and an open development process.

AURA-1 is **not** intended to compete directly with frontier-scale models. Its goal is to be useful, efficient and deeply integrated with the AURA ecosystem.

## Development roadmap

- [x] M001 — Project initialization
- [ ] M002 — AURA-Dataset v0.1
- [ ] M003 — First QLoRA training
- [ ] M004 — AURA-1-v0.1
- [ ] M005 — Evaluation and benchmarks
- [ ] M006 — Ollama integration
- [ ] M007 — AURA desktop integration
- [ ] M008 — Hugging Face publication
- [ ] M009 — Open-source release

## Repository structure

```text
AURA-1/
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── training/
│   ├── train.py
│   ├── config.yaml
│   └── requirements.txt
├── evaluation/
│   ├── benchmark.py
│   └── prompts.json
├── inference/
│   └── test_model.py
├── ollama/
│   └── Modelfile
├── docs/
│   ├── architecture.md
│   ├── dataset.md
│   └── roadmap.md
├── MODEL_CARD.md
└── LICENSE
```

## License

The final project license will be defined before the first public model release. Until then, model, dataset and dependency licenses must be tracked separately.

## Disclaimer

AURA-1 is an experimental research and development project. Model quality, safety and capabilities may change significantly during development.

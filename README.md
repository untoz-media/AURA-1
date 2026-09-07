# AURA-1

**AURA-1** is a local personal-assistant application and experimental model
project developed by **Untoz**.

> **Status:** Alpha 0.1 — local browser and terminal application

## Project

- **Name:** AURA-1
- **Organization:** Untoz
- **Project:** AURA
- **Model type:** Large Language Model (LLM)
- **Current runtime model:** Qwen3-4B-Instruct-2507
- **Target size:** ~4B parameters
- **Initial fine-tuning approach:** QLoRA
- **Primary language:** English
- **Additional language:** Portuguese (European Portuguese)
- **Runtime target:** Ollama / local inference
- **Current release:** AURA-1 0.1.0-alpha.1 application
- **Future model release:** separately trained AURA-1 artifact

## Goals

AURA-1 is intended to be a compact, capable and efficient model that can act as the language brain of AURA. The project prioritizes local use, practical assistant capabilities, Portuguese quality and an open development process.

AURA-1 is **not** intended to compete directly with frontier-scale models. Its goal is to be useful, efficient and deeply integrated with the AURA ecosystem.

The current Alpha uses the unmodified `Qwen/Qwen3-4B-Instruct-2507` weights.
Untoz currently provides the AURA identity, interface, memory, orchestration and
tools. This Alpha must not be described as a separately trained Untoz model.

## Usar a AURA-1 no navegador

No Windows, faz duplo clique em `iniciar_aura_web.bat`. Em alternativa:

```powershell
python aura_web.py
```

O navegador abre em `http://127.0.0.1:8765`. Mantém a janela do terminal
aberta enquanto usas a AURA. O primeiro arranque demora enquanto o modelo
local é carregado. A interface só aceita ligações do próprio computador.

A versão atual oferece conversa local, memória, cálculo, data e hora,
informação do sistema e consulta controlada de nomes de ficheiros do projeto.
Para usar outra porta: `python aura_web.py --port 9000`.

O modo de terminal continua disponível com `python aura.py`.

Para uma instalação nova, instala primeiro uma versão de PyTorch adequada ao
teu computador e depois executa:

```powershell
python -m pip install -r requirements-runtime.txt
```

Consulta [docs/web.md](docs/web.md) para instruções, funcionalidades e limites.

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

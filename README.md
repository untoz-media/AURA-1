# AURA-1

> **AI that lives on your computer.**

**AURA-1** is a local-first personal AI assistant and experimental AI project developed by **Untoz**.

The goal is simple: build an assistant that can run on your own computer, understand your system, use local tools, remember useful context, and evolve into a practical desktop AI without depending on massive cloud infrastructure.

> **Current release:** AURA-1 Alpha 0.1 — public pre-release

---

## What is AURA-1?

AURA-1 is the first public generation of the AURA assistant.

It combines a local language model runtime with an Untoz-built assistant layer that provides the interface, memory, orchestration, tools, system integration and product experience around the model.

AURA-1 is designed around a **local-first** philosophy:

- Runs on the user's own computer
- Keeps local interaction as the default
- Can access approved local tools and system information
- Does not require Untoz to operate a large GPU cloud for basic use
- Is designed to become more capable through modular tools and future local models

The current Alpha is experimental and is intended for early testing, development and feedback.

---

## AURA-1 Alpha 0.1

**Alpha 0.1** is the first public pre-release of AURA-1.

Current capabilities include:

- Local AI chat
- Browser-based local interface
- Terminal interface
- Persistent assistant memory
- Calculator tools
- Date and time tools
- System information tools
- Controlled access to project file names
- Local-only web interface binding
- Support for English and European Portuguese interactions

AURA-1 is still in active development. Features, behaviour, UI, model configuration and compatibility may change between Alpha releases.

---

## Current AI model

AURA-1 Alpha 0.1 currently uses:

`Qwen/Qwen3-4B-Instruct-2507`

The current Alpha uses the upstream model weights without an Untoz-trained AURA checkpoint.

Untoz currently provides the **AURA identity, interface, assistant logic, memory, orchestration and tools** around the model.

For transparency, **AURA-1 Alpha 0.1 should not be described as a separately trained Untoz foundation model**.

A separately trained AURA-1 model is planned as a future project milestone.

---

## Project information

| | |
|---|---|
| **Name** | AURA-1 |
| **Developer** | Untoz |
| **Project family** | AURA |
| **Current release** | Alpha 0.1 |
| **Release type** | Public pre-release |
| **Architecture** | Local-first personal AI assistant |
| **Current runtime model** | Qwen3-4B-Instruct-2507 |
| **Target model size** | ~4B parameters |
| **Planned fine-tuning approach** | QLoRA |
| **Primary language** | English |
| **Additional focus** | European Portuguese |
| **Runtime target** | Local inference / Ollama-compatible workflows |

---

## Run AURA-1 locally

### Web interface

On Windows, double-click:

```text
iniciar_aura_web.bat
```

Or start it manually:

```powershell
python aura_web.py
```

The local interface opens at:

```text
http://127.0.0.1:8765
```

Keep the terminal window open while using AURA-1.

The first startup may take longer while the local model is loaded into memory.

The web interface is bound to the local computer by default and does not accept external network connections.

To use another port:

```powershell
python aura_web.py --port 9000
```

### Terminal interface

The terminal version is also available:

```powershell
python aura.py
```

---

## Installation

AURA-1 is currently aimed primarily at Windows development and testing environments.

Install a PyTorch build appropriate for your hardware, then install the runtime dependencies:

```powershell
python -m pip install -r requirements-runtime.txt
```

See [`docs/web.md`](docs/web.md) for additional setup information, current functionality and limitations.

---

## Local-first architecture

AURA-1 is being built around the idea that useful personal AI should be able to operate directly on consumer hardware.

```text
AURA-1 Interface
       │
       ▼
AURA Assistant Layer
       │
       ├── Memory
       ├── Tools
       ├── System integration
       └── Orchestration
       │
       ▼
Local AI Runtime
       │
       ▼
CPU / GPU on the user's computer
```

This architecture allows AURA to grow without requiring every interaction to be processed by centralized Untoz servers.

Future versions may introduce optional hybrid or cloud-assisted capabilities, while maintaining local-first operation as a core part of the project.

---

## Development goals

AURA-1 is intended to become a compact, capable and practical personal assistant that is deeply integrated with the computer it runs on.

The project prioritizes:

- Local execution
- Practical assistant capabilities
- System and tool integration
- Privacy-conscious architecture
- Strong European Portuguese support
- Efficient operation on consumer hardware
- Transparent development
- A modular architecture that can improve over time

AURA-1 is **not intended to compete directly with frontier-scale cloud models**.

Its goal is different: to become a useful AI that belongs on your computer.

---

## Roadmap

- [x] **M001** — Project initialization
- [x] **Alpha 0.1** — First public AURA application pre-release
- [ ] **M002** — AURA Dataset v0.1
- [ ] **M003** — First QLoRA training
- [ ] **M004** — First separately trained AURA-1 model checkpoint
- [ ] **M005** — Evaluation and benchmarks
- [ ] **M006** — Expanded local runtime / Ollama integration
- [ ] **M007** — Native desktop integration
- [ ] **M008** — Hugging Face publication
- [ ] **M009** — Broader open-source release

The roadmap is experimental and may change as AURA develops.

---

## Repository structure

```text
AURA-1/
├── aura.py
├── aura_web.py
├── aura/
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
│   ├── roadmap.md
│   └── web.md
├── MODEL_CARD.md
├── requirements-runtime.txt
└── LICENSE
```

---

## Brand

**AURA-1** is part of the Untoz technology ecosystem.

**Brand line:**

> AI that lives on your computer.

AURA is designed to feel calm, precise, local and deeply integrated with the device it runs on.

---

## Alpha warning

AURA-1 Alpha 0.1 is experimental pre-release software.

You should expect:

- Bugs
- Incomplete features
- Performance differences between computers
- Model limitations and incorrect responses
- Breaking changes between Alpha versions

Do not rely on AURA-1 Alpha for critical, safety-sensitive or irreversible tasks.

---

## License

The final project license will be defined before the first public AURA-trained model release.

Until then, the software, model, dataset and third-party dependency licenses must be considered separately.

The current runtime model remains subject to its own upstream license and terms.

---

## About Untoz

AURA-1 is developed by **Untoz** as part of its technology and AI projects.

**AURA-1 Alpha 0.1 marks the beginning of the public AURA journey.**

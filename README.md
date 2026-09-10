# AURA-1

<p align="center">
  <img src="assets/aura-mark.svg" alt="AURA mark" width="220" />
</p>

<p align="center">
  <strong>AI that lives on your computer.</strong>
</p>

<p align="center">
  <a href="https://aura.untoz.site/">Official website</a>
</p>

**AURA-1** is a local-first personal AI assistant and experimental AI project developed by **Untoz**.

The goal is to build an assistant that runs on your own computer, understands relevant system state, uses approved local tools, remembers useful context and can carry out bounded multi-step work without handing control of the device to an unrestricted agent.

> **Public release:** AURA-1 Alpha 0.1  
> **Current development line:** Alpha 2 · Intelligent Agent Runtime v1.4

---

## Download the Windows app

Tagged releases are prepared to publish two Windows packages from GitHub Releases:

- **`AURA-1-<version>-windows-x64.zip`** — native desktop application containing `AURA-1.exe` and its runtime folder.
- **`AURA-1-<version>-windows-source.zip`** — source package, documentation and installation scripts.

Each ZIP is accompanied by a **SHA-256 checksum**.

For the desktop package, extract the complete folder and run:

```text
AURA-1.exe
```

The desktop app is built as a one-folder application for reliability with local ML dependencies. Keep the extracted files together.

The upstream model weights are intentionally **not bundled** in GitHub releases. On first use, AURA may need to download the configured local model, which requires several gigabytes of disk space.

See [`docs/desktop-app.md`](docs/desktop-app.md) for the desktop architecture, build flow and privacy boundary.

---

## What is AURA-1?

AURA-1 combines a local language model runtime with an Untoz-built assistant layer providing the product interface, memory, planning, permissions, tools, system integration and recovery logic around the model.

AURA is designed around a **local-first** philosophy:

- Runs on the user's own computer
- Keeps local interaction as the default
- Uses approved local tools and bounded computer state
- Does not require an Untoz GPU cloud for normal local use
- Keeps destructive actions behind explicit permission boundaries
- Can grow through modular tools and future local models

The current Alpha is experimental and intended for testing, development and feedback.

---

## Alpha 2 Agent Runtime

The current development branch includes the v1.4 Intelligent Agent Runtime and connects it to the actual AURA application.

Current capabilities include:

- Local AI chat
- Native Windows desktop host and browser fallback
- Persistent assistant memory
- App Launcher and App Discovery
- Process inspection and protected process closing
- Safe folder creation
- CPU, RAM, battery, foreground-process and system-pressure awareness
- Deterministic fast paths for common computer requests
- Intelligent Planner for bounded multi-step requests
- State-aware preflight to avoid redundant actions
- Result-aware single-pass recovery after recoverable failures
- One-time confirmation UI for protected actions
- English as the primary product language with European Portuguese support

The app renders plans and execution results directly in the conversation, while permission decisions remain in the backend.

---

## Safety model

AURA does **not** give the language model unrestricted access to the operating system.

The current agent architecture uses:

```text
User request
    │
    ▼
Deterministic Planner / Tool Router
    │
    ▼
Intelligent Planner when needed
    │
    ▼
StateObserver + SystemState
    │
    ▼
PlanExecutor / ActionExecutor
    │
    ▼
PermissionManager
    │
    ├── READ          → allowed
    ├── ACTION        → allowed bounded action
    ├── DESTRUCTIVE   → explicit user confirmation
    └── BLOCKED       → rejected
    │
    ▼
Result inspection → at most one constrained recovery pass
```

Shell, PowerShell and CMD execution remain outside the planner allowlist. A high CPU value, low battery, low disk space or any other observation does not grant additional permissions.

---

## Local privacy boundary

The desktop UI is backed by an HTTP service bound only to `127.0.0.1`. Requests are checked for local Host/Origin values.

The system-awareness panel intentionally does **not** collect:

- Window titles
- Clipboard contents
- Process command lines
- Environment variables
- Usernames
- File contents

Foreground awareness is limited to the foreground process name. Process telemetry is bounded to information such as process name, PID and memory usage.

---

## Current AI model

AURA-1 currently uses:

`Qwen/Qwen3-4B-Instruct-2507`

The Alpha uses upstream model weights without an Untoz-trained AURA checkpoint. Untoz currently provides the **AURA identity, interface, assistant logic, memory, orchestration, safety layers and tools** around the model.

For transparency, AURA-1 Alpha should not be described as a separately trained Untoz foundation model. A separately trained/fine-tuned AURA checkpoint remains a future project milestone.

---

## Run from source

### Native desktop app

On Windows:

```powershell
python -m pip install -r requirements-desktop.txt
python aura_desktop.py
```

### Browser fallback

```powershell
python aura_web.py
```

The local interface opens on `127.0.0.1` and does not accept external network connections.

### Terminal interface

```powershell
python aura.py
```

Install a PyTorch build appropriate for your hardware when needed, then install the runtime dependencies:

```powershell
python -m pip install -r requirements-runtime.txt
```

---

## Build a Windows desktop package

After installing the desktop runtime and PyInstaller:

```powershell
python -m pip install -r requirements-desktop.txt
python -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File scripts/build_desktop.ps1
```

This produces a Windows x64 ZIP and SHA-256 checksum under `dist/`.

GitHub's `Publish AURA release` workflow performs the same build automatically for tags matching `v*` and publishes the source and desktop packages as a pre-release.

---

## Project information

| | |
|---|---|
| **Name** | AURA-1 |
| **Developer** | Untoz |
| **Project family** | AURA |
| **Website** | [aura.untoz.site](https://aura.untoz.site/) |
| **Release type** | Experimental public pre-release |
| **Architecture** | Local-first personal AI assistant |
| **Agent Runtime** | v1.4 development |
| **Current runtime model** | Qwen3-4B-Instruct-2507 |
| **Target model size** | ~4B parameters |
| **Planned fine-tuning approach** | QLoRA |
| **Primary language** | English |
| **Additional focus** | European Portuguese |
| **Primary desktop target** | Windows x64 |

---

## Repository structure

```text
AURA-1/
├── aura.py                  # terminal interface
├── aura_web.py              # browser fallback
├── aura_desktop.py          # native desktop host
├── aura/
│   ├── agent/               # planning, permissions, execution, recovery
│   ├── tools/               # local tools and system awareness
│   ├── web/                 # app backend + static product UI
│   ├── memory/
│   └── model/
├── assets/
├── docs/
│   └── desktop-app.md
├── scripts/
│   ├── build_release.py
│   └── build_desktop.ps1
├── tests/
├── requirements-runtime.txt
├── requirements-desktop.txt
└── MODEL_CARD.md
```

---

## Roadmap

- [x] **M001** — Project initialization
- [x] **Alpha 0.1** — First public AURA application pre-release
- [x] **Agent Runtime v1.1–v1.4** — planning, state awareness and bounded recovery
- [x] **Initial native desktop integration** — Agent Runtime available through the app
- [ ] **M002** — AURA Dataset v0.1
- [ ] **M003** — First QLoRA training
- [ ] **M004** — First separately trained AURA-1 checkpoint
- [ ] **M005** — Evaluation and broader stability testing
- [ ] **Installer / updater** — polished first-run setup and update flow
- [ ] **Release candidate** — hardened Windows app for the official 1.0 launch
- [ ] **Hugging Face publication**
- [ ] **Broader open-source release**

---

## Brand

**AURA-1** is part of the Untoz technology ecosystem.

> **AI that lives on your computer.**

AURA is designed to feel calm, precise, local and deeply integrated with the device it runs on.

---

## Alpha warning

AURA-1 is experimental pre-release software. Expect bugs, incomplete features, performance differences between computers, model limitations and breaking changes between Alpha versions.

Do not rely on AURA-1 Alpha for critical, safety-sensitive or irreversible tasks.

---

## License

The software, model, dataset and third-party dependency licenses must be considered separately. The current runtime model remains subject to its upstream license and terms. See `LICENSE`, `NOTICE` and `MODEL_CARD.md` for repository-specific information.

---

## About Untoz

AURA-1 is developed by **Untoz** as part of its technology and AI projects.

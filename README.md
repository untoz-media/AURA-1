# AURA-1

**AURA-1** is an open-source local AI assistant developed by **Untoz**.

AURA is designed to live on your computer, combine local AI with safe desktop tools, and help with everyday work without requiring every request to be sent to a cloud service.

> **Alpha software:** AURA-1 is under active development. Features, APIs and behavior may change between builds.

## Alpha 2 — Intelligent Agent Runtime

The current Alpha 2 development branch introduces a layered local-agent runtime:

1. **Deterministic Planner** for known multi-step workflows.
2. **Tool Router v2** for fast single-tool requests.
3. **Intelligent Planner** for flexible natural-language computer actions.
4. **State Observer** for read-only awareness of relevant local state.
5. **Plan Executor / Action Executor** for validated execution.
6. **Permission Manager** for allowlisting and explicit confirmation of protected actions.

### State-aware execution

AURA can inspect a narrow read-only view of the computer before planning and again immediately before an action executes. This lets the runtime avoid redundant work such as reopening an application that is already running, trying to close an application that is already closed, or recreating a folder that already exists.

The planning snapshot is only a hint and may become stale. The execution-time preflight is authoritative. State observation never grants permissions, never authorizes cleanup or deletion, and never turns a read observation into a destructive action.

Examples:

```text
You: Prepara-me para editar vídeo.
AURA: observes relevant application and disk state -> plans only the actions still needed

You: Abre o OBS.
AURA: OBS já estava em execução — não voltei a abrir.

You: Fecha o Bloco de Notas.
AURA: if already closed, no destructive confirmation is requested
```

## Safety model

AURA does not give the local model unrestricted access to the operating system. The model proposes only structured actions from a strict allowlist. Shell, PowerShell and CMD execution are not exposed to the planner. Unknown tools, unexpected arguments and invalid structured plans are rejected.

Protected actions, such as terminating a running process, still require explicit confirmation. Each destructive action in a multi-step plan requires its own confirmation.

## Current agent actions

The Alpha 2 planner can currently propose:

- `disk_info.info`
- `system_info.info`
- `app_launcher.open`
- `process_manager.list`
- `process_manager.is_running`
- `process_manager.close`
- `file_manager.create_folder`

This list is intentionally small while the agent runtime is being hardened.

## Context and memory

AURA keeps normal conversation memory and persistent user memory separate from agent-planning context. The Intelligent Planner uses a small ephemeral context window for direct follow-ups such as “fecha-o” or “abre também o Notion”. That context is not written to persistent memory and is cleared with `/clear`.

## Local model

AURA-1 currently targets a local Qwen-based runtime. Install a PyTorch build appropriate for your hardware, then install the runtime dependencies:

```powershell
python -m pip install -r requirements-runtime.txt
```

The project is designed to support local execution on consumer hardware. Performance depends heavily on the selected model, quantization and GPU/CPU configuration.

## Run the terminal assistant

```powershell
python aura.py
```

Useful commands include:

```text
/help
/info
/memory
/memory-search TEXTO
/remember CHAVE VALOR
/forget CHAVE
/clear-memory
/profiles
/profile fast|balanced|deep
/settings
/tools
/clear
/exit
```

## Browser interface

AURA also includes a local browser interface. See [`docs/web.md`](docs/web.md) for setup information, current functionality and limitations.

## Testing

The focused Alpha 2 agent suite validates the Intelligent Planner, resilient plan execution and state-aware preflight without loading the real Qwen model:

```powershell
python -m pytest -q tests/test_intelligent_planner.py tests/test_plan_executor.py tests/test_state_observer.py
```

The GitHub Actions workflow also compiles the relevant runtime modules before running these tests.

## Repository structure

```text
aura/
  agent/
    action_executor.py
    intelligent_planner.py
    permission_manager.py
    plan_executor.py
    planner.py
    state_observer.py
    tool_router.py
  core/
  memory/
  model/
  tools/
  ui/
tests/
docs/
scripts/
```

## Project status

AURA-1 is experimental and should not yet be treated as a fully autonomous desktop agent. The current engineering goal is controlled local agency: observe a narrow state, build a validated plan, ask permission where needed, execute through explicit tools, and fail safely.

## License

See [`LICENSE`](LICENSE), [`NOTICE`](NOTICE) and [`MODEL_CARD.md`](MODEL_CARD.md) for project licensing and model information.

---

Developed by **Untoz**.

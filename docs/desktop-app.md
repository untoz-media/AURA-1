# AURA-1 Desktop App

AURA-1 Alpha 2 exposes the Intelligent Agent Runtime through the same local interface used by the desktop application. The UI is served only on loopback (`127.0.0.1`) and the native Windows window is hosted by pywebview.

## First-run experience

Alpha 2 starts light. On a new installation, AURA does **not** load or download the language model before the user completes setup.

The first-run flow is:

1. **Welcome** — explains local-first operation, state awareness and permission boundaries.
2. **Computer check** — reads only the hardware facts needed for compatibility: logical CPU count, total/available RAM, free disk space and optional CUDA GPU/VRAM information.
3. **Model setup** — lets the user choose `Fast`, `Balanced` or `Deep`. Balanced is the default recommendation.
4. **Privacy and control** — requires acknowledgement of local-processing behaviour and the protected-action permission boundary.
5. **Prepare AURA** — only now does the app start the local model runtime. If the configured model is not already cached, the upstream runtime may download several GB before AURA becomes ready.

The setup file is stored locally at `data/settings/first_run.json` for the current Alpha portable/source layout. It contains the selected profile and setup acknowledgements, not conversations or model output.

### Hardware compatibility gate

The Alpha 2 first-run check currently uses a conservative product baseline:

- **8 GB RAM minimum**; 16 GB recommended.
- **12 GB free disk minimum** before model setup; 20 GB recommended for breathing room, cache and updates.
- **4 GB VRAM recommended** when CUDA acceleration is available.
- CPU-only operation is not blocked, but the UI warns that local inference can be significantly slower.
- The native Alpha 2 desktop experience is primarily tested on Windows.

`ready`, `limited` and `unsupported` are compatibility hints, not benchmark scores. AURA blocks model setup only when a hard minimum such as RAM or free disk is not met.

## What works in the app

The app uses the v1.4 agent pipeline rather than bypassing it with a direct chat call. Natural-language requests can therefore use deterministic routines, Tool Router fast paths, Intelligent Planner, StateObserver, SystemState telemetry, PlanExecutor, PermissionManager and the single-pass RecoveryPlanner.

Protected actions are never approved by the frontend. The backend returns a short-lived confirmation token and the user must explicitly choose **Allow once** or **Cancel**. Starting a new conversation discards any pending confirmation.

The sidebar can read bounded local telemetry: CPU, RAM, pressure classification, battery state and foreground process name. This is read-only and does not grant any new action permissions.

## Privacy boundary

The app server binds only to localhost and validates Host/Origin. The state panel and first-run hardware check do not expose window titles, clipboard contents, process command lines, environment variables, usernames or file contents. Model conversations and tool execution remain local by default.

Model files are not bundled with AURA. If they are missing locally, the configured upstream model provider/runtime may need a network connection to obtain them during model setup.

## Failure behaviour

If model startup fails after setup, AURA preserves the setup choices and shows a retry state. The user can retry loading the model without granting additional tool permissions. Failure to load a model does not automatically trigger cleanup, app closing or any destructive recovery action.

## Run from source

Install the normal runtime plus the desktop host:

```powershell
python -m pip install -r requirements-desktop.txt
python aura_desktop.py
```

For a packaged source download, `instalar_aura_windows.bat` prepares the private environment and `iniciar_aura.bat` opens the desktop app.

## GitHub release package

Tagged releases build two Windows downloads:

- `AURA-1-<version>-windows-source.zip` — source package and installation scripts.
- `AURA-1-<version>-windows-x64.zip` — native desktop bundle containing `AURA-1.exe` and its runtime files.

The desktop ZIP deliberately does **not** include model weights. A model can be several gigabytes and remains managed by the local model runtime/cache. Every ZIP is published with a `.sha256` checksum.

## Build locally on Windows

```powershell
python -m pip install -r requirements-desktop.txt
python -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File scripts/build_desktop.ps1
```

The build is one-folder rather than one-file because large ML runtimes are more reliable and faster to start in this format. Keep the complete extracted `AURA-1` folder together.

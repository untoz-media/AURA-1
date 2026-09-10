# AURA-1 Desktop App

AURA-1 Alpha 2 exposes the Intelligent Agent Runtime through the same local interface used by the desktop application. The UI is served only on loopback (`127.0.0.1`) and the native Windows window is hosted by pywebview.

## What works in the app

The app uses the v1.4 agent pipeline rather than bypassing it with a direct chat call. Natural-language requests can therefore use deterministic routines, Tool Router fast paths, Intelligent Planner, StateObserver, SystemState telemetry, PlanExecutor, PermissionManager and the single-pass RecoveryPlanner.

Protected actions are never approved by the frontend. The backend returns a short-lived confirmation token and the user must explicitly choose **Allow once** or **Cancel**. Starting a new conversation discards any pending confirmation.

The sidebar can read bounded local telemetry: CPU, RAM, pressure classification, battery state and foreground process name. This is read-only and does not grant any new action permissions.

## Privacy boundary

The app server binds only to localhost and validates Host/Origin. The state panel does not expose window titles, clipboard contents, command lines, environment variables, usernames or file contents. Model conversations and tool execution remain local.

## Run from source

Install the normal runtime plus the desktop host:

```powershell
python -m pip install -r requirements-desktop.txt
python aura_desktop.py
```

The first model startup may need to download the configured model if it is not already cached locally.

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

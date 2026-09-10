# AURA-1 Alpha 2 — Intelligent Agent App

Version: `0.2.0-alpha.1`

This Alpha 2 development line brings the AURA Intelligent Agent Runtime into the actual local application and adds a native Windows desktop host.

## App integration

- Native AURA desktop window powered by pywebview
- Localhost-only application service; no external network binding
- Agent Runtime v1.4 available from the app instead of direct-chat-only behaviour
- Deterministic Planner and Tool Router fast paths
- Intelligent Planner for bounded multi-step requests
- State-aware execution and redundant-action preflight
- Result-aware single-pass recovery
- One-time confirmation UI for protected actions
- CPU, RAM, system-pressure, battery and foreground-process panel
- App launching, App Discovery, process checks, safe folder creation and existing memory features

## Safety and privacy

Protected actions are not approved by JavaScript or by the model. The backend issues a short-lived confirmation token and the user must explicitly select **Allow once** before execution continues. Shell, PowerShell and CMD execution remain outside the planner allowlist.

The system-state panel is read-only. It does not collect window titles, clipboard contents, process command lines, environment variables, usernames or file contents.

## Windows downloads

A tagged `v0.2.0-alpha.1` GitHub pre-release is configured to publish:

- `AURA-1-0.2.0-alpha.1-windows-source.zip`
- `AURA-1-0.2.0-alpha.1-windows-x64.zip`
- SHA-256 checksum files for both packages

The native desktop ZIP contains `AURA-1.exe` and its runtime folder. Extract the complete folder and launch `AURA-1.exe`.

The source ZIP contains a Windows installer. Run `instalar_aura_windows.bat`; it installs the desktop dependencies into a private `.venv`, creates a desktop shortcut when possible and keeps `iniciar_aura.bat` as a fallback launcher.

The upstream `Qwen/Qwen3-4B-Instruct-2507` model weights are **not** bundled in the release. The first startup may download the configured model and requires several gigabytes of disk space.

This remains experimental Alpha software. Do not rely on it for critical, safety-sensitive or irreversible tasks.

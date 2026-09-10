# AURA-1 Alpha 2 — Intelligent Agent App

Version: `0.2.0-alpha.1`

This Alpha 2 development line brings the AURA Intelligent Agent Runtime into the actual local application, adds a native Windows desktop host and introduces a guided first-run setup before the local model is loaded.

## First-run setup

- AURA now starts light on a new installation instead of immediately loading or downloading the model.
- Guided flow: **Welcome → Computer Check → Model Setup → Privacy & Control → Ready**.
- Hardware compatibility check reads only logical CPU count, RAM, free storage and optional CUDA GPU/VRAM information.
- Product baseline: 8 GB RAM minimum, 16 GB recommended; 12 GB free disk minimum, 20 GB recommended; 4 GB VRAM recommended when CUDA acceleration is available.
- Computers below hard RAM/storage minimums are blocked before model setup rather than failing halfway through a large model load.
- Users can choose `Fast`, `Balanced` or `Deep`; Balanced is the default recommendation.
- Local-processing information and the protected-action permission boundary must be acknowledged before the model starts.
- If the model fails to load, the app preserves setup choices and offers a safe retry without granting new permissions.

## App integration

- Native AURA desktop window powered by pywebview.
- Localhost-only application service; no external network binding.
- Agent Runtime v1.4 available from the app instead of direct-chat-only behaviour.
- Deterministic Planner and Tool Router fast paths.
- Intelligent Planner for bounded multi-step requests.
- State-aware execution and redundant-action preflight.
- Result-aware single-pass recovery.
- One-time confirmation UI for protected actions.
- CPU, RAM, system-pressure, battery and foreground-process panel.
- App launching, App Discovery, process checks, safe folder creation and existing memory features.

## Safety and privacy

Protected actions are not approved by JavaScript or by the model. The backend issues a short-lived confirmation token and the user must explicitly select **Allow once** before execution continues. Shell, PowerShell and CMD execution remain outside the planner allowlist.

The system-state panel and first-run hardware check are read-only. They do not collect window titles, clipboard contents, process command lines, environment variables, usernames or file contents.

The setup record stores the selected profile and setup acknowledgements locally. It does not store conversations or model output.

## Windows downloads

A tagged `v0.2.0-alpha.1` GitHub pre-release is configured to publish:

- `AURA-1-0.2.0-alpha.1-windows-source.zip`
- `AURA-1-0.2.0-alpha.1-windows-x64.zip`
- SHA-256 checksum files for both packages

The native desktop ZIP contains `AURA-1.exe` and its runtime folder. Extract the complete folder and launch `AURA-1.exe`.

The source ZIP contains a Windows installer. Run `instalar_aura_windows.bat`; it installs the desktop dependencies into a private `.venv`, creates a desktop shortcut when possible and keeps `iniciar_aura.bat` as a fallback launcher.

The upstream `Qwen/Qwen3-4B-Instruct-2507` model weights are **not** bundled in the release. During the final setup step, the local runtime may download the configured model if it is not already cached and requires several gigabytes of disk space.

This remains experimental Alpha software. Do not rely on it for critical, safety-sensitive or irreversible tasks.

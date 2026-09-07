@echo off
cd /d "%~dp0"
title AURA-1 Web
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" aura_web.py
) else (
  python aura_web.py
)
if errorlevel 1 (
  echo.
  echo A AURA-1 terminou com um erro. Confirma a mensagem acima.
  pause
)

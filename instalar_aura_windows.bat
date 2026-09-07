@echo off
cd /d "%~dp0"
title Instalar AURA-1 Alpha
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows.ps1"
if errorlevel 1 (
  echo.
  echo A instalacao terminou com um erro. Confirma a mensagem acima.
  pause
  exit /b 1
)
echo.
echo Instalacao concluida. Podes abrir iniciar_aura_web.bat.
pause

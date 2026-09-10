@echo off
cd /d "%~dp0"
title Instalar AURA-1 Alpha 2
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows.ps1"
if errorlevel 1 (
  echo.
  echo A instalacao terminou com um erro. Confirma a mensagem acima.
  pause
  exit /b 1
)
echo.
echo Instalacao concluida.
echo Abre o atalho AURA-1 Alpha 2 ou executa iniciar_aura.bat.
echo iniciar_aura_web.bat continua disponivel como modo de compatibilidade.
pause

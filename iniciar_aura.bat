@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo AURA-1 ainda nao esta instalada nesta pasta.
  echo Executa primeiro instalar_aura_windows.bat.
  pause
  exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0aura_desktop.py"

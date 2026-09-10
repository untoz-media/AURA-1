$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python nao foi encontrado. Instala Python 3.11 ou mais recente e volta a executar este instalador."
}

$VersionText = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$VersionParts = $VersionText.Split('.')
if ([int]$VersionParts[0] -lt 3 -or ([int]$VersionParts[0] -eq 3 -and [int]$VersionParts[1] -lt 11)) {
    throw "A AURA-1 requer Python 3.11 ou mais recente. Foi encontrado Python $VersionText."
}

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    Write-Host "A criar o ambiente privado da AURA-1..."
    & python -m venv .venv
}

$AuraPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$AuraPythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
Write-Host "A instalar a AURA-1 Desktop e as dependencias locais..."
& $AuraPython -m pip install --upgrade pip
& $AuraPython -m pip install -r requirements-desktop.txt

if (-not (Test-Path -LiteralPath $AuraPythonw)) {
    throw "A instalacao terminou sem encontrar pythonw.exe no ambiente da AURA-1."
}

$Launcher = Join-Path $ProjectRoot "aura_desktop.py"
$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "AURA-1 Alpha 2.lnk"
try {
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $AuraPythonw
    $Shortcut.Arguments = ('"{0}"' -f $Launcher)
    $Shortcut.WorkingDirectory = $ProjectRoot
    $Shortcut.Description = "AURA-1 Alpha 2 by Untoz"
    $Shortcut.Save()
    Write-Host "Atalho criado no Ambiente de Trabalho."
} catch {
    Write-Warning "Nao foi possivel criar o atalho. Podes usar iniciar_aura.bat."
}

Write-Host ""
Write-Host "AURA-1 Alpha 2 instalada com sucesso." -ForegroundColor Green
Write-Host "Abre o atalho AURA-1 Alpha 2 ou executa iniciar_aura.bat."
Write-Host "No primeiro arranque, o modelo Qwen pode ser descarregado e ocupar varios GB."

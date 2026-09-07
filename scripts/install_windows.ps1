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
Write-Host "A instalar as dependencias da AURA-1..."
& $AuraPython -m pip install --upgrade pip
& $AuraPython -m pip install -r requirements-runtime.txt

Write-Host ""
Write-Host "AURA-1 Alpha instalada com sucesso." -ForegroundColor Green
Write-Host "No primeiro arranque, o modelo Qwen sera descarregado e pode ocupar varios GB."

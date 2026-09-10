$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Version = (python -c "from aura import __version__; print(__version__)").Trim()
$DistRoot = Join-Path $Root "dist"
$BuildRoot = Join-Path $Root "build"
$DesktopRoot = Join-Path $BuildRoot "desktop"
$WorkRoot = Join-Path $BuildRoot "pyinstaller"
$StaticRoot = Join-Path $Root "aura\web\static"
$AssetsRoot = Join-Path $Root "assets"

if (-not (Test-Path $StaticRoot)) {
    throw "AURA web static assets were not found at $StaticRoot"
}
if (-not (Test-Path $AssetsRoot)) {
    throw "AURA brand assets were not found at $AssetsRoot"
}

New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null
Remove-Item -Recurse -Force $DesktopRoot -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $WorkRoot -ErrorAction SilentlyContinue

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name "AURA-1" `
  --distpath $DesktopRoot `
  --workpath $WorkRoot `
  --specpath $BuildRoot `
  --add-data "${StaticRoot};aura/web/static" `
  --add-data "${AssetsRoot};assets" `
  --collect-all webview `
  --collect-all bitsandbytes `
  --hidden-import aura.core.assistant `
  --hidden-import aura.model.qwen `
  aura_desktop.py

$Bundle = Join-Path $DesktopRoot "AURA-1"
$Executable = Join-Path $Bundle "AURA-1.exe"
if (-not (Test-Path $Executable)) {
    throw "PyInstaller did not produce AURA-1.exe"
}

$Zip = Join-Path $DistRoot "AURA-1-$Version-windows-x64.zip"
Remove-Item -Force $Zip -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $Bundle "*") -DestinationPath $Zip -CompressionLevel Optimal

$Hash = (Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLowerInvariant()
$Checksum = "$Zip.sha256"
"$Hash  $([System.IO.Path]::GetFileName($Zip))" | Set-Content -Encoding ascii $Checksum

Write-Host "Built $Zip"
Write-Host "Executable: $Executable"

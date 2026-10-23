$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $PSScriptRoot "iniciar-quiqu.ps1"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Quiqu.ia.lnk"
$powershell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

if (-not (Test-Path $launcher)) {
  throw "No encuentro el lanzador: $launcher"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $powershell
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$launcher`""
$shortcut.WorkingDirectory = $repo
$shortcut.Description = "Abrir Quiqu.ia"
$shortcut.WindowStyle = 1
$shortcut.Save()

Write-Host "Acceso directo creado en: $shortcutPath" -ForegroundColor Green

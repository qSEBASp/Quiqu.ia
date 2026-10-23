$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $PSScriptRoot "iniciar-quiqu.ps1"
$hiddenLauncher = Join-Path $PSScriptRoot "iniciar-quiqu-oculto.vbs"
$icon = Join-Path $repo "apps\web\app\favicon.ico"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Quiqu.ia.lnk"
$wscript = Join-Path $env:SystemRoot "System32\wscript.exe"

if (-not (Test-Path $launcher)) {
  throw "No encuentro el lanzador: $launcher"
}

if (-not (Test-Path $hiddenLauncher)) {
  throw "No encuentro el lanzador oculto: $hiddenLauncher"
}

if (-not (Test-Path $icon)) {
  throw "No encuentro el icono: $icon"
}

if (-not (Test-Path $wscript)) {
  throw "No encuentro wscript.exe: $wscript"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $wscript
$shortcut.Arguments = "//Nologo `"$hiddenLauncher`""
$shortcut.WorkingDirectory = $repo
$shortcut.Description = "Abrir Quiqu.ia"
$shortcut.WindowStyle = 1
$shortcut.IconLocation = "$icon,0"
$shortcut.Save()

Write-Host "Acceso directo creado en: $shortcutPath" -ForegroundColor Green

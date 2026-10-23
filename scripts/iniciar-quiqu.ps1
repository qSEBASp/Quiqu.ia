$ErrorActionPreference = "Stop"

try {
  $Host.UI.RawUI.WindowTitle = "Quiqu.ia"
} catch {}

$repo = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $repo ".runtime"
$stopFile = Join-Path $runtime "stop"
$serverPidFile = Join-Path $runtime "server.pid"
$browserProfile = Join-Path $runtime "edge-profile"

function Test-QuiquUrl {
  param([string]$Url)

  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 1
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
}

function Get-EdgePath {
  $candidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
    (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe")
  )

  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
      return $candidate
    }
  }

  return $null
}

function Open-Quiqu {
  $edge = Get-EdgePath
  if ($edge) {
    Start-Process -FilePath $edge -ArgumentList @(
      "--app=http://127.0.0.1:3000",
      "--user-data-dir=$browserProfile",
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-sync",
      "--window-size=1280,900"
    ) | Out-Null
    return
  }

  Start-Process "http://127.0.0.1:3000" | Out-Null
}

function Close-QuiquBrowser {
  if (-not (Test-Path $browserProfile)) {
    return
  }

  Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*$browserProfile*" } |
    ForEach-Object {
      Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

$venv = Join-Path $repo "apps\api\.venv\Scripts\python.exe"
$webModules = Join-Path $repo "apps\web\node_modules"

if (-not (Test-Path $venv)) {
  Write-Host "No encuentro el entorno de Python de apps/api." -ForegroundColor Red
  Write-Host "Ejecuta primero la instalacion descrita en el README." -ForegroundColor Red
  Read-Host "Pulsa Enter para salir"
  exit 1
}

if (-not (Test-Path $webModules)) {
  Write-Host "No encuentro las dependencias web." -ForegroundColor Red
  Write-Host "Ejecuta: npm install --prefix apps/web" -ForegroundColor Red
  Read-Host "Pulsa Enter para salir"
  exit 1
}

New-Item -ItemType Directory -Force -Path $runtime | Out-Null

$apiUp = Test-QuiquUrl "http://127.0.0.1:8000/api/health"
$webUp = Test-QuiquUrl "http://127.0.0.1:3000"

if ($apiUp -and $webUp) {
  Write-Host "Quiqu.ia ya esta en marcha. Abriendo la pagina..." -ForegroundColor Green
  Open-Quiqu
  Start-Sleep -Seconds 1
  exit 0
}

if ($apiUp -or $webUp) {
  Write-Host "Hay una parte de Quiqu.ia ya en marcha (API: $apiUp, web: $webUp)." -ForegroundColor Yellow
  Write-Host "Cierra la ventana anterior de Quiqu.ia o reinicia el PC antes de volver a abrirla." -ForegroundColor Yellow
  Read-Host "Pulsa Enter para salir"
  exit 1
}

Remove-Item -LiteralPath $stopFile -Force -ErrorAction SilentlyContinue

$env:QUIQU_STOP_FILE = $stopFile

Write-Host "Iniciando Quiqu.ia..." -ForegroundColor Cyan
Write-Host "Los datos se quedan en tu PC." -ForegroundColor DarkGray
Write-Host "Usa el boton de la pagina o cierra esta ventana para detenerlo." -ForegroundColor DarkGray

$serverProcess = Start-Process -FilePath $env:ComSpec -ArgumentList '/d /s /c "npm run dev"' -WorkingDirectory $repo -NoNewWindow -PassThru
Set-Content -LiteralPath $serverPidFile -Value $serverProcess.Id -Encoding ascii

$opened = $false
$deadline = (Get-Date).AddSeconds(90)

try {
  while (-not $serverProcess.HasExited -and (Get-Date) -lt $deadline) {
    if (Test-Path $stopFile) {
      break
    }

    if (
      -not $opened -and
      (Test-QuiquUrl "http://127.0.0.1:3000") -and
      (Test-QuiquUrl "http://127.0.0.1:8000/api/health")
    ) {
      Open-Quiqu
      $opened = $true
      Write-Host "Quiqu.ia esta listo: http://127.0.0.1:3000" -ForegroundColor Green
    }

    Start-Sleep -Milliseconds 500
  }

  if (-not $opened -and -not $serverProcess.HasExited -and -not (Test-Path $stopFile)) {
    Write-Host "No he podido confirmar que la app este lista. Abriendo igualmente..." -ForegroundColor Yellow
    Open-Quiqu
    $opened = $true
  }

  while (-not $serverProcess.HasExited) {
    if (Test-Path $stopFile) {
      break
    }

    Start-Sleep -Milliseconds 500
  }

  if (Test-Path $stopFile) {
    Remove-Item -LiteralPath $stopFile -Force -ErrorAction SilentlyContinue
    Write-Host "Cerrando Quiqu.ia..." -ForegroundColor Yellow
    Start-Sleep -Milliseconds 700
  }
} finally {
  Close-QuiquBrowser
  if (-not $serverProcess.HasExited) {
    & taskkill.exe /PID $serverProcess.Id /T /F | Out-Null
  }
  Remove-Item -LiteralPath $serverPidFile -Force -ErrorAction SilentlyContinue
}

Write-Host "Quiqu.ia se ha detenido." -ForegroundColor Green
Start-Sleep -Milliseconds 800

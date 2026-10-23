$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $repo ".runtime"
$stopFile = Join-Path $runtime "stop"
$serverPidFile = Join-Path $runtime "server.pid"
$browserProfile = Join-Path $runtime "edge-profile"
$logFile = Join-Path $runtime "quiqu.log"
$devOutLog = Join-Path $runtime "dev.out.log"
$devErrLog = Join-Path $runtime "dev.err.log"

New-Item -ItemType Directory -Force -Path $runtime | Out-Null

function Write-QuiquLog {
  param(
    [string]$Message,
    [string]$Level = "INFO"
  )

  $line = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
  try {
    Add-Content -LiteralPath $logFile -Value $line -Encoding utf8
  } catch {}

  Write-Host $Message
}

function Show-QuiquError {
  param([string]$Message)

  Write-QuiquLog $Message "ERROR"

  try {
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
    [System.Windows.Forms.MessageBox]::Show(
      "$Message`n`nDetalles en:`n$logFile",
      "Quiqu.ia",
      [System.Windows.Forms.MessageBoxButtons]::OK,
      [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
  } catch {}
}

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
  $candidates = @()

  if (${env:ProgramFiles(x86)}) {
    $candidates += Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"
  }

  if ($env:ProgramFiles) {
    $candidates += Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"
  }

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
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

    Write-QuiquLog "Abriendo Quiqu.ia en Edge (modo app)."
    return $true
  }

  Write-QuiquLog "Edge no encontrado. Abriendo en el navegador predeterminado." "WARN"
  Start-Process "http://127.0.0.1:3000" | Out-Null
  return $false
}

function Get-QuiquBrowserProcesses {
  if (-not (Test-Path $browserProfile)) {
    return
  }

  Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*$browserProfile*" }
}

function Close-QuiquBrowser {
  @(Get-QuiquBrowserProcesses) | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
}

$venv = Join-Path $repo "apps\api\.venv\Scripts\python.exe"
$webModules = Join-Path $repo "apps\web\node_modules"
$serverProcess = $null
$cleanupNeeded = $false

try {
  Write-QuiquLog "Comprobando el entorno de Quiqu.ia."

  if (-not (Test-Path $venv)) {
    Show-QuiquError "No encuentro el entorno de Python de apps/api. Ejecuta primero la instalacion descrita en el README."
    exit 1
  }

  if (-not (Test-Path $webModules)) {
    Show-QuiquError "No encuentro las dependencias web. Ejecuta: npm install --prefix apps/web"
    exit 1
  }

  $apiUp = Test-QuiquUrl "http://127.0.0.1:8000/api/health"
  $webUp = Test-QuiquUrl "http://127.0.0.1:3000"

  if ($apiUp -and $webUp) {
    Write-QuiquLog "Quiqu.ia ya esta en marcha. Abriendo la pagina."
    Open-Quiqu | Out-Null
    Start-Sleep -Seconds 1
    exit 0
  }

  if ($apiUp -or $webUp) {
    Show-QuiquError "Hay una parte de Quiqu.ia ya en marcha (API: $apiUp, web: $webUp). Cierra la ventana anterior o reinicia el PC antes de volver a abrirla."
    exit 1
  }

  Remove-Item -LiteralPath $stopFile -Force -ErrorAction SilentlyContinue

  $env:QUIQU_STOP_FILE = $stopFile

  Write-QuiquLog "Iniciando Quiqu.ia."
  Write-QuiquLog "Los datos se quedan en tu PC. Usa el boton de la pagina para detenerlo."

  $serverProcess = Start-Process -FilePath $env:ComSpec -ArgumentList '/d /s /c "npm run dev"' -WorkingDirectory $repo -NoNewWindow -RedirectStandardOutput $devOutLog -RedirectStandardError $devErrLog -PassThru
  $cleanupNeeded = $true
  Set-Content -LiteralPath $serverPidFile -Value $serverProcess.Id -Encoding ascii

  $opened = $false
  $deadline = (Get-Date).AddSeconds(90)

  while (-not $serverProcess.HasExited -and (Get-Date) -lt $deadline) {
    if (Test-Path $stopFile) {
      break
    }

    if (
      -not $opened -and
      (Test-QuiquUrl "http://127.0.0.1:3000") -and
      (Test-QuiquUrl "http://127.0.0.1:8000/api/health")
    ) {
      Open-Quiqu | Out-Null
      $opened = $true
      Write-QuiquLog "Quiqu.ia esta listo: http://127.0.0.1:3000"
    }

    Start-Sleep -Milliseconds 500
  }

  if (-not $opened -and -not $serverProcess.HasExited -and -not (Test-Path $stopFile)) {
    Write-QuiquLog "No he podido confirmar que la app este lista. Abriendo igualmente." "WARN"
    Open-Quiqu | Out-Null
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
    Write-QuiquLog "Cerrando Quiqu.ia."
    Start-Sleep -Milliseconds 700
  } elseif (-not $opened) {
    Show-QuiquError "Quiqu.ia no pudo arrancar. Revisa el log para ver el error."
  } else {
    Show-QuiquError "Quiqu.ia se detuvo de forma inesperada. Revisa el log para ver el error."
  }
} catch {
  Show-QuiquError "No se pudo iniciar Quiqu.ia: $($_.Exception.Message)"
  exit 1
} finally {
  if ($cleanupNeeded) {
    Close-QuiquBrowser

    if ($serverProcess -and -not $serverProcess.HasExited) {
      & taskkill.exe /PID $serverProcess.Id /T /F | Out-Null
    }

    Remove-Item -LiteralPath $serverPidFile -Force -ErrorAction SilentlyContinue
  }
}

Write-QuiquLog "Quiqu.ia se ha detenido."
Start-Sleep -Milliseconds 500

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

function Wait-QuiquReady {
  param([int]$Seconds = 120)

  $deadline = (Get-Date).AddSeconds($Seconds)

  while ((Get-Date) -lt $deadline) {
    if (
      (Test-QuiquUrl "http://127.0.0.1:3000") -and
      (Test-QuiquUrl "http://127.0.0.1:8000/api/health")
    ) {
      return $true
    }

    Start-Sleep -Milliseconds 500
  }

  return $false
}

function Request-QuiquMutex {
  param(
    [System.Threading.Mutex]$Mutex,
    [int]$TimeoutMilliseconds = 0
  )

  try {
    return $Mutex.WaitOne($TimeoutMilliseconds)
  } catch [System.Threading.AbandonedMutexException] {
    return $true
  }
}

function Get-QuiquOwnedProcesses {
  $markers = @(
    "iniciar-quiqu.ps1",
    "uvicorn",
    "next dev",
    "next-server",
    "concurrently"
  )

  $owned = @()

  foreach ($process in (Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
    $command = $process.CommandLine

    if (-not $command) {
      continue
    }

    if ($process.ProcessId -eq $PID) {
      continue
    }

    if ($command -notlike "*$repo*") {
      continue
    }

    foreach ($marker in $markers) {
      if ($command -like "*$marker*") {
        $owned += $process
        break
      }
    }
  }

  return $owned
}

function Stop-QuiquProcessTree {
  param([int]$ProcessId)

  if (-not $ProcessId -or $ProcessId -eq $PID) {
    return
  }

  try {
    & taskkill.exe /PID $ProcessId /T /F 2>&1 | Out-Null
  } catch {}
}

function Stop-QuiquLeftovers {
  $owned = @(Get-QuiquOwnedProcesses)
  $launchers = @($owned | Where-Object { $_.CommandLine -like "*iniciar-quiqu.ps1*" })
  $others = @($owned | Where-Object { $_.CommandLine -notlike "*iniciar-quiqu.ps1*" })

  # Primero el lanzador colgado: si matamos su arbol antes, muestra un error modal.
  foreach ($process in $launchers) {
    Stop-QuiquProcessTree $process.ProcessId
  }

  if (Test-Path $serverPidFile) {
    $rawPid = (Get-Content -LiteralPath $serverPidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    $parsedPid = 0

    if ([int]::TryParse("$rawPid".Trim(), [ref]$parsedPid)) {
      Stop-QuiquProcessTree $parsedPid
    }

    Remove-Item -LiteralPath $serverPidFile -Force -ErrorAction SilentlyContinue
  }

  foreach ($process in $others) {
    Stop-QuiquProcessTree $process.ProcessId
  }
}

function Test-QuiquStartupFailure {
  if (-not (Test-Path $devOutLog)) {
    return $false
  }

  try {
    $tail = Get-Content -LiteralPath $devOutLog -Tail 30 -ErrorAction Stop
  } catch {
    return $false
  }

  foreach ($line in $tail) {
    if ($line -like "*exited with code 1*") {
      return $true
    }

    if ($line -like "*EADDRINUSE*") {
      return $true
    }

    if ($line -like "*error while attempting to bind*") {
      return $true
    }

    if ($line -like "*Application startup failed*") {
      return $true
    }
  }

  return $false
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

function Get-QuiquBrowserWindows {
  $windows = @()

  foreach ($process in (Get-Process -Name "msedge" -ErrorAction SilentlyContinue)) {
    if (-not $process.MainWindowTitle) {
      continue
    }

    $command = (Get-CimInstance Win32_Process -Filter "ProcessId = $($process.Id)" -ErrorAction SilentlyContinue).CommandLine

    if ($command -and $command -like "*$browserProfile*") {
      $windows += $process
    }
  }

  return $windows
}

function Open-Quiqu {
  $existing = @(Get-QuiquBrowserWindows)

  if ($existing.Count -gt 0) {
    Write-QuiquLog "Quiqu.ia ya tiene una ventana abierta. La traigo al frente."

    try {
      $shell = New-Object -ComObject WScript.Shell
      $shell.AppActivate($existing[0].Id) | Out-Null
    } catch {
      Write-QuiquLog "No he podido traer la ventana al frente." "WARN"
    }

    return $true
  }

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
$mutexName = "Global\QuiquIaLauncher"
$mutex = New-Object System.Threading.Mutex($false, $mutexName)
$mutexAcquired = $false

try {
  $mutexAcquired = Request-QuiquMutex $mutex 0

  if (-not $mutexAcquired) {
    if ((Test-QuiquUrl "http://127.0.0.1:3000") -and (Test-QuiquUrl "http://127.0.0.1:8000/api/health")) {
      Write-QuiquLog "Quiqu.ia ya esta en marcha. Abriendo la pagina."
      Open-Quiqu | Out-Null
      exit 0
    }

    Write-QuiquLog "Quiqu.ia ya se esta abriendo. Espero a que este lista."

    if (Wait-QuiquReady 30) {
      # La otra instancia abre su ventana al quedar lista; le doy un momento
      # para que la deteccion de ventana no falle por una carrera.
      Start-Sleep -Seconds 2
      Open-Quiqu | Out-Null
      Write-QuiquLog "Quiqu.ia esta listo: http://127.0.0.1:3000"
      exit 0
    }

    Write-QuiquLog "La ejecucion anterior no responde. Reiniciando Quiqu.ia." "WARN"
    Stop-QuiquLeftovers
    Start-Sleep -Seconds 2

    $mutexAcquired = Request-QuiquMutex $mutex 5000

    if (-not $mutexAcquired) {
      Show-QuiquError "Quiqu.ia no responde y no he podido reiniciarlo. Espera unos segundos y vuelve a intentarlo."
      exit 1
    }
  }

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
    Write-QuiquLog "Hay restos de una ejecucion anterior (API: $apiUp, web: $webUp). Limpiando." "WARN"
    Stop-QuiquLeftovers
    Start-Sleep -Seconds 1

    $apiUp = Test-QuiquUrl "http://127.0.0.1:8000/api/health"
    $webUp = Test-QuiquUrl "http://127.0.0.1:3000"

    if ($apiUp -or $webUp) {
      Show-QuiquError "Hay un programa usando el puerto 8000 o el 3000 (API: $apiUp, web: $webUp) y no es de Quiqu.ia. Cierralo y vuelve a intentarlo."
      exit 1
    }
  }

  Remove-Item -LiteralPath $stopFile -Force -ErrorAction SilentlyContinue

  $env:QUIQU_STOP_FILE = $stopFile

  Write-QuiquLog "Iniciando Quiqu.ia."
  Write-QuiquLog "Los datos se quedan en tu PC. Usa el boton de la pagina para detenerlo."

  $serverProcess = Start-Process -FilePath $env:ComSpec -ArgumentList '/d /s /c "npm run dev"' -WorkingDirectory $repo -NoNewWindow -RedirectStandardOutput $devOutLog -RedirectStandardError $devErrLog -PassThru
  $cleanupNeeded = $true
  Set-Content -LiteralPath $serverPidFile -Value $serverProcess.Id -Encoding ascii

  $opened = $false
  $startupFailed = $false
  $deadline = (Get-Date).AddSeconds(120)

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

    if (-not $opened -and (Test-QuiquStartupFailure)) {
      $startupFailed = $true
      break
    }

    Start-Sleep -Milliseconds 500
  }

  if (
    -not $opened -and
    -not $startupFailed -and
    -not $serverProcess.HasExited -and
    -not (Test-Path $stopFile)
  ) {
    if (Wait-QuiquReady 30) {
      Open-Quiqu | Out-Null
      $opened = $true
      Write-QuiquLog "Quiqu.ia esta listo: http://127.0.0.1:3000"
    } else {
      $startupFailed = $true
    }
  }

  if ($startupFailed -and -not (Test-Path $stopFile)) {
    throw "No se pudo iniciar el servidor web. Puede que otro programa este usando el puerto 3000 o el 8000."
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
      Stop-QuiquProcessTree $serverProcess.Id
    }

    Remove-Item -LiteralPath $serverPidFile -Force -ErrorAction SilentlyContinue
  }

  if ($mutexAcquired) {
    try {
      $mutex.ReleaseMutex()
    } catch {}
  }

  $mutex.Dispose()
}

Write-QuiquLog "Quiqu.ia se ha detenido."
Start-Sleep -Milliseconds 500

# run_all.ps1 - starts backend + Flutter from ONE terminal window

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$backendDir = $root
$flutterDir = Join-Path $root "flutter_app"

Write-Host "=== Starting LensGuide backend (main.py) ===" -ForegroundColor Cyan

$backendArgs = @{
    FilePath         = "python"
    ArgumentList     = "main.py"
    WorkingDirectory = $backendDir
    NoNewWindow      = $true
    PassThru         = $true
}

$backendProcess = Start-Process @backendArgs

Write-Host "Backend PID: $($backendProcess.Id) - waiting 3s for it to boot..." -ForegroundColor DarkGray
Start-Sleep -Seconds 3

try {
    Write-Host ""
    Write-Host "=== Starting Flutter app ===" -ForegroundColor Cyan
    Set-Location $flutterDir
    flutter run
}
finally {
    Write-Host ""
    Write-Host "=== Flutter exited - stopping backend (PID $($backendProcess.Id)) ===" -ForegroundColor Yellow
    if (-not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }
    Set-Location $root
}
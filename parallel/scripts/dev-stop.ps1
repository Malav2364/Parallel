$ErrorActionPreference = "SilentlyContinue"

$root = Split-Path -Parent $PSScriptRoot
$logRoot = Join-Path $root "logs"

Write-Host ""
Write-Host "Stopping PIOS services..."

# Stop PIOS development processes
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue |
    Stop-Process -Force

Get-Process -Name "python" -ErrorAction SilentlyContinue |
    Stop-Process -Force

# Give processes a moment to release log files
Start-Sleep -Seconds 1

# Clear development logs
if (Test-Path -LiteralPath $logRoot) {

    Write-Host "Clearing logs..."

    Get-ChildItem `
        -LiteralPath $logRoot `
        -File `
        -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================"
Write-Host " PIOS Development Environment Stopped"
Write-Host "========================================"
Write-Host ""

if (Test-Path -LiteralPath $logRoot) {
    $remainingLogs = Get-ChildItem `
        -LiteralPath $logRoot `
        -File `
        -ErrorAction SilentlyContinue

    if ($remainingLogs.Count -eq 0) {
        Write-Host "Logs cleared."
    }
    else {
        Write-Host "Warning: Some log files could not be removed."
    }
}
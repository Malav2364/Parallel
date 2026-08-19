$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

$services = @(
    @{
        Name = "Gateway"
        Path = Join-Path $root "services\gateway"
        Port = 8000
    },
    @{
        Name = "Identity"
        Path = Join-Path $root "services\identity"
        Port = 8001
    },
    @{
        Name = "Projects"
        Path = Join-Path $root "services\projects"
        Port = 8002
    },
    @{
        Name = "Spaces"
        Path = Join-Path $root "services\spaces"
        Port = 8003
    },
    @{
        Name = "Context"
        Path = Join-Path $root "services\context"
        Port = 8004
    },
    @{
        Name = "Goals"
        Path = Join-Path $root "services\goals"
        Port = 8005
    },
    @{
        Name = "Habits"
        Path = Join-Path $root "services\habits"
        Port = 8006
    },
    @{
        Name = "Notifications"
        Path = Join-Path $root "services\notifications"
        Port = 8007
    },
    @{
        Name = "Reminders"
        Path = Join-Path $root "services\reminders"
        Port = 8008
    }
)

foreach ($service in $services) {
    if (-not (Test-Path -LiteralPath $service.Path -PathType Container)) {
        throw "Service directory not found: $($service.Path)"
    }
}

foreach ($service in $services) {
    Write-Host "Starting $($service.Name) on port $($service.Port)..."

    $command = @(
        "Set-Location -LiteralPath '$($service.Path)'"
        "uv run uvicorn app.main:app --reload --port $($service.Port)"
    ) -join "; "

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit"
        "-Command"
        $command
    )
}

Write-Host ""
Write-Host "PIOS development services started."
Write-Host "Gateway  : http://localhost:8000"
Write-Host "Identity : http://localhost:8001"
Write-Host "Projects : http://localhost:8002"
Write-Host "Spaces   : http://localhost:8003"
Write-Host "Context  : http://localhost:8004"
Write-Host "Goals  : http://localhost:8005"
Write-Host "Habits  : http://localhost:8006"
Write-Host "Notifications  : http://localhost:8007"
Write-Host "Reminders  : http://localhost:8008"

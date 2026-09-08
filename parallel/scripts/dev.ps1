$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logRoot = Join-Path $root "logs"

if (-not (Test-Path -LiteralPath $logRoot)) {
    New-Item -ItemType Directory -Path $logRoot | Out-Null
}

$services = @(
    @{
        Name = "Gateway"
        Path = Join-Path $root "services\gateway"
        Port = 8000
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Identity"
        Path = Join-Path $root "services\identity"
        Port = 8001
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Projects"
        Path = Join-Path $root "services\projects"
        Port = 8002
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Spaces"
        Path = Join-Path $root "services\spaces"
        Port = 8003
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Context"
        Path = Join-Path $root "services\context"
        Port = 8004
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Goals"
        Path = Join-Path $root "services\goals"
        Port = 8005
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Habits"
        Path = Join-Path $root "services\habits"
        Port = 8006
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Notifications"
        Path = Join-Path $root "services\notifications"
        Port = 8007
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Reminders"
        Path = Join-Path $root "services\reminders"
        Port = 8008
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "Github"
        Path = Join-Path $root "services\github"
        Port = 8009
        App = "app.main:app"
        Type = "api"
    },
    @{
        Name = "ReminderWorker"
        Path = Join-Path $root "services\reminders"
        Port = $null
        App = $null
        Type = "worker"
    }
)

# --------------------------------------------------
# Validate service directories
# --------------------------------------------------

foreach ($service in $services) {
    if (-not (Test-Path -LiteralPath $service.Path -PathType Container)) {
        throw "Service directory not found: $($service.Path)"
    }
}

# --------------------------------------------------
# Start services as background processes
# --------------------------------------------------

$processes = @()

foreach ($service in $services) {

    $name = $service.Name
    $path = $service.Path
    $logFile = Join-Path $logRoot "$name.log"

    if ($service.Type -eq "api") {

        Write-Host "Starting $name on port $($service.Port)..."

        $arguments = @(
            "uv"
            "run"
            "uvicorn"
            $service.App
            "--reload"
            "--port"
            $service.Port
        )

    }
    elseif ($service.Type -eq "worker") {

        Write-Host "Starting Reminder Worker..."

        $arguments = @(
            "uv"
            "run"
            "python"
            "-m"
            "app.worker"
        )
    }

    $process = Start-Process `
        -FilePath "cmd.exe" `
        -ArgumentList @(
            "/c"
            "cd /d `"$path`" && $($arguments -join ' ') >> `"$logFile`" 2>&1"
        ) `
        -WindowStyle Hidden `
        -PassThru

    $processes += @{
        Name = $name
        Process = $process
        Log = $logFile
    }
}

# --------------------------------------------------
# Startup summary
# --------------------------------------------------

Write-Host ""
Write-Host "========================================"
Write-Host " PIOS Development Environment"
Write-Host "========================================"
Write-Host ""

foreach ($service in $services) {

    if ($service.Type -eq "api") {
        Write-Host (
            "{0,-15} http://localhost:{1}" -f `
            $service.Name, `
            $service.Port
        )
    }
    else {
        Write-Host (
            "{0,-15} background worker" -f `
            $service.Name
        )
    }
}

Write-Host ""
Write-Host "Logs:"
Write-Host "  $logRoot"
Write-Host ""
Write-Host "All services are running in the background."
Write-Host "Use .\stop.ps1 to stop the PIOS stack."
Write-Host ""
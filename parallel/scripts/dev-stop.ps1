$ErrorActionPreference = "SilentlyContinue"

$ports = @(8000, 8001, 8002, 8003, 8004)
$stopped = @{}

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen

    foreach ($connection in $connections) {
        $processId = $connection.OwningProcess

        if (-not $stopped.ContainsKey($processId)) {
            Stop-Process -Id $processId -Force
            $stopped[$processId] = $true
            Write-Host "Stopped process $processId on port $port"
        }
    }
}

if ($stopped.Count -eq 0) {
    Write-Host "No PIOS development services were listening on ports 8000-8004."
} else {
    Write-Host "PIOS development services stopped."
}

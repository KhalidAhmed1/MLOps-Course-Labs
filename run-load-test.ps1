# Load testing helper script for Locust

param(
    [string]$Command = "web",
    [string]$Host = "http://localhost:8000",
    [int]$Users = 10,
    [int]$SpawnRate = 1,
    [string]$RunTime = "5m",
    [string]$MasterHost = "localhost",
    [int]$MasterPort = 5557
)

# Function to display usage
function Show-Usage {
    Write-Host "`nLoad Testing Helper - Locust CLI Wrapper`n" -ForegroundColor Cyan
    Write-Host "Usage: .\run-load-test.ps1 -Command <command> [Options]`n"
    Write-Host "Commands:"
    Write-Host "    web         Run Locust with web UI"
    Write-Host "    headless    Run Locust in headless mode"
    Write-Host "    distributed Run distributed load testing (master)"
    Write-Host "    worker      Run as worker node"
    Write-Host "    help        Show this help message"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "    -Host URL           API endpoint (default: http://localhost:8000)"
    Write-Host "    -Users NUM          Number of users (default: 10)"
    Write-Host "    -SpawnRate NUM      Users per second (default: 1)"
    Write-Host "    -RunTime TIME       Test duration, e.g., 5m, 30s (headless only)"
    Write-Host "    -MasterHost HOST    Master IP/hostname"
    Write-Host "    -MasterPort PORT    Master port (default: 5557)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "    # Web UI against local API"
    Write-Host "    .\run-load-test.ps1 -Command web"
    Write-Host ""
    Write-Host "    # Headless against EC2"
    Write-Host "    .\run-load-test.ps1 -Command headless -Host http://54.123.45.67:8000 -Users 100 -SpawnRate 10 -RunTime 5m"
    Write-Host ""
    Write-Host "    # Distributed master"
    Write-Host "    .\run-load-test.ps1 -Command distributed -Host http://54.123.45.67:8000"
    Write-Host ""
    Write-Host "    # Worker node"
    Write-Host "    .\run-load-test.ps1 -Command worker -MasterHost master-ip`n"
}

# Check if locust is installed
try {
    $null = locust --version 2>&1
} catch {
    Write-Host "Locust not found. Installing..." -ForegroundColor Yellow
    pip install locust
}

# Execute command
switch ($Command) {
    "web" {
        Write-Host "Starting Locust Web UI..." -ForegroundColor Green
        Write-Host "Host: $Host" -ForegroundColor Cyan
        Write-Host "Open browser to: http://localhost:8089" -ForegroundColor Cyan
        & locust -f locustfile.py --host=$Host
    }
    "headless" {
        Write-Host "Starting Locust Headless..." -ForegroundColor Green
        Write-Host "Host: $Host" -ForegroundColor Cyan
        Write-Host "Users: $Users" -ForegroundColor Cyan
        Write-Host "Spawn Rate: $SpawnRate" -ForegroundColor Cyan
        Write-Host "Duration: $RunTime" -ForegroundColor Cyan
        & locust -f locustfile.py `
            --host=$Host `
            --users=$Users `
            --spawn-rate=$SpawnRate `
            --run-time=$RunTime `
            --headless
    }
    "distributed" {
        Write-Host "Starting Locust Master (Distributed Mode)..." -ForegroundColor Green
        Write-Host "Host: $Host" -ForegroundColor Cyan
        & locust -f locustfile.py `
            --host=$Host `
            --master `
            --web `
            --expect-workers=2
    }
    "worker" {
        Write-Host "Starting Locust Worker..." -ForegroundColor Green
        Write-Host "Master Host: $MasterHost" -ForegroundColor Cyan
        Write-Host "Master Port: $MasterPort" -ForegroundColor Cyan
        & locust -f locustfile.py `
            --worker `
            --master-host=$MasterHost `
            --master-port=$MasterPort
    }
    "help" {
        Show-Usage
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Usage
        exit 1
    }
}

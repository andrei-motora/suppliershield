#!/usr/bin/env pwsh
# SupplierShield one-command launcher (Windows / PowerShell)
# Installs deps if needed, generates data if missing, then starts backend + frontend.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# 1. Python deps
Write-Step "Checking Python dependencies"
$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }
& $pythonCmd -m pip install -q -r requirements.txt

# 2. Synthetic data
if (-not (Test-Path "data/raw/suppliers.csv")) {
    Write-Step "Generating synthetic data"
    & $pythonCmd scripts/generate_data.py
} else {
    Write-Step "Data already present (skipping generation)"
}

# 3. Frontend deps
if (-not (Test-Path "frontend/node_modules")) {
    Write-Step "Installing frontend dependencies"
    Push-Location frontend
    npm install
    Pop-Location
} else {
    Write-Step "Frontend dependencies already installed"
}

# 4. Launch backend + frontend in separate windows
Write-Step "Starting backend on http://localhost:8001"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; & $pythonCmd -m uvicorn backend.main:app --reload --port 8001"

Write-Step "Starting frontend on http://localhost:5173"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$root/frontend'; npm run dev:frontend"

Write-Host ""
Write-Host "SupplierShield is starting up." -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8001" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Close the two spawned windows to stop the servers." -ForegroundColor Yellow

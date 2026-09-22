#!/usr/bin/env bash
# SupplierShield one-command launcher (macOS / Linux)
# Installs deps if needed, generates data if missing, then starts backend + frontend.

set -e
cd "$(dirname "$0")"

step() { printf "\033[36m==> %s\033[0m\n" "$1"; }

PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON="python"

# 1. Python deps
step "Checking Python dependencies"
"$PYTHON" -m pip install -q -r requirements.txt

# 2. Synthetic data
if [ ! -f "data/raw/suppliers.csv" ]; then
    step "Generating synthetic data"
    "$PYTHON" scripts/generate_data.py
else
    step "Data already present (skipping generation)"
fi

# 3. Frontend deps
if [ ! -d "frontend/node_modules" ]; then
    step "Installing frontend dependencies"
    (cd frontend && npm install)
else
    step "Frontend dependencies already installed"
fi

# 4. Launch backend + frontend, stop both on Ctrl+C
step "Starting backend on http://localhost:8001"
"$PYTHON" -m uvicorn backend.main:app --reload --port 8001 &
BACKEND_PID=$!

step "Starting frontend on http://localhost:5173"
(cd frontend && npm run dev:frontend) &
FRONTEND_PID=$!

cleanup() {
    echo ""
    step "Shutting down"
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup INT TERM

echo ""
printf "\033[32mSupplierShield is running.\033[0m\n"
printf "\033[32m  Backend:  http://localhost:8001\033[0m\n"
printf "\033[32m  Frontend: http://localhost:5173\033[0m\n"
printf "\033[33mPress Ctrl+C to stop.\033[0m\n\n"

wait

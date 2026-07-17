#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Elite Bridge — Install ==="

# ── Python / uv ──────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    if [ -f "$HOME/.local/bin/uv" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    else
        echo "uv not found. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi

echo "Using uv: $(uv --version)"

# Backend venv
echo "── Setting up backend venv ──"
uv venv "$ROOT/backend/.venv"
(
    cd "$ROOT/backend"
    uv pip install -e ".[dev]"
)

# ── Node / npm ───────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    echo "Node.js not found. Please install Node.js >= 18."
    exit 1
fi

echo "Using node: $(node --version)"

# Frontend dependencies
echo "── Installing frontend dependencies ──"
(
    cd "$ROOT/frontend"
    npm install
)

# ── Build frontend for production ────────────────────────────────
echo "── Building frontend ──"
(
    cd "$ROOT/frontend"
    npx vite build
)

echo ""
echo "=== Install complete ==="
echo "  Start with:  ./scripts/start.sh"

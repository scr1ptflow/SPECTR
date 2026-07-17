#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── uv in PATH ───────────────────────────────────────────────────
export PATH="$HOME/.local/bin:$PATH"

DEV=false
if [ "${1:-}" = "--dev" ] || [ "${1:-}" = "-d" ]; then
    DEV=true
fi

cleanup() {
    echo ""
    echo "Shutting down..."
    kill "$BACKEND_PID" 2>/dev/null || true
    if [ "$DEV" = true ] && [ -n "${FRONTEND_PID:-}" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── Backend ──────────────────────────────────────────────────────
source "$ROOT/backend/.venv/bin/activate"
cd "$ROOT"
PYTHONPATH=backend python -m bridge_core.main &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID) → http://127.0.0.1:8420"

# ── Frontend dev server (optional) ──────────────────────────────
if [ "$DEV" = true ]; then
    (
        cd "$ROOT/frontend"
        npm run dev
    ) &
    FRONTEND_PID=$!
    echo "Frontend dev server started (PID $FRONTEND_PID) → http://127.0.0.1:5173"
    echo ""
    echo "  Dev mode:  open http://127.0.0.1:5173"
else
    echo ""
    echo "  Production: open http://127.0.0.1:8420"
    echo "  Dev mode:   ./scripts/start.sh --dev"
fi

echo "Press Ctrl+C to stop."
wait "$BACKEND_PID"

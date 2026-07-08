#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
REQUIREMENTS=("textual")

if [ ! -d "$VENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

MISSING=false
for pkg in "${REQUIREMENTS[@]}"; do
    if ! "$VENV/bin/python" -c "import $pkg" 2>/dev/null; then
        MISSING=true
        break
    fi
done

if [ "$MISSING" = true ]; then
    echo "Installing dependencies..."
    "$VENV/bin/pip" install --quiet "${REQUIREMENTS[@]}"
fi

exec "$VENV/bin/python" "$DIR/main.py"

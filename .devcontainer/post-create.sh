#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

unset VIRTUAL_ENV

echo "Project root: $(pwd)"
echo "Synchronizing Python environment..."

uv python install
uv sync

if [[ -f frontend/package-lock.json ]]; then
    echo "Synchronizing frontend dependencies..."
    npm --prefix frontend ci
fi

echo "Environment synchronized successfully."
#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

unset VIRTUAL_ENV

echo "Project root: $(pwd)"
echo "Synchronizing Python environment..."

uv sync

echo "Environment synchronized successfully."
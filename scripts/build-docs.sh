#!/usr/bin/env bash
# Build the static documentation site from docs_src/ into target/site/.
# The Docs workflow builds and publishes the same site to GitHub Pages.
#
# Usage: ./scripts/build-docs.sh [--serve]
#   --serve  Serve the site at http://127.0.0.1:8000 and rebuild on change
#
# Requires mkdocs and the material theme:
#   pip install --user mkdocs mkdocs-material
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v mkdocs >/dev/null 2>&1; then
    echo "error: mkdocs is not installed. Install with: pip install --user mkdocs mkdocs-material" >&2
    exit 1
fi

case "${1:-}" in
    --serve) exec mkdocs serve ;;
    "") ;;
    *) echo "error: unknown argument: $1" >&2; exit 1 ;;
esac

mkdocs build --clean --strict

echo "Built docs into: $ROOT_DIR/target/site/"

#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
ROOT="/workspace/v0.0/code"

cd "${ROOT}"

bootstrap() {
  python -m pip install --upgrade pip
  python -m pip install -e ".[dev,bench,diagram,music,voice-optional]"
}

run_tests() {
  pytest -q tests
}

case "${MODE}" in
  bootstrap-only)
    bootstrap
    ;;
  test-only)
    run_tests
    ;;
  all)
    bootstrap
    run_tests
    ;;
  *)
    echo "Unknown MODE: ${MODE}"
    echo "Usage: $0 [bootstrap-only|test-only|all]"
    exit 2
    ;;
esac

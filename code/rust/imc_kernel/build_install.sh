#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${ROOT_DIR}/../../.." && pwd)"
DEFAULT_PYTHON="${REPO_ROOT}/.venv/bin/python"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  SELECTED_PYTHON="${PYTHON_BIN}"
elif [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  SELECTED_PYTHON="${VIRTUAL_ENV}/bin/python"
elif [[ -x "${DEFAULT_PYTHON}" ]]; then
  SELECTED_PYTHON="${DEFAULT_PYTHON}"
else
  SELECTED_PYTHON="$(command -v python3 || true)"
fi

if [[ -z "${SELECTED_PYTHON}" || ! -x "${SELECTED_PYTHON}" ]]; then
  echo "unable to locate a usable python interpreter; activate a venv or set PYTHON_BIN" >&2
  exit 1
fi

PYTHON_BIN="${SELECTED_PYTHON}"

PY_PLATFORM="$("${PYTHON_BIN}" - <<'PY'
import sysconfig
print(sysconfig.get_platform())
PY
)"

case "${PY_PLATFORM}" in
  *x86_64*)
    TARGET_TRIPLE="x86_64-apple-darwin"
    ;;
  *arm64*)
    TARGET_TRIPLE="aarch64-apple-darwin"
    ;;
  *)
    echo "unsupported python platform: ${PY_PLATFORM}" >&2
    exit 1
    ;;
esac

WHEEL_DIR="${ROOT_DIR}/target/wheels/${TARGET_TRIPLE}"
mkdir -p "${WHEEL_DIR}"

"${PYTHON_BIN}" -m pip install --disable-pip-version-check --quiet maturin
rustup target add "${TARGET_TRIPLE}" >/dev/null 2>&1 || true
"${PYTHON_BIN}" -m maturin build --release --manifest-path "${ROOT_DIR}/Cargo.toml" --interpreter "${PYTHON_BIN}" --target "${TARGET_TRIPLE}" --out "${WHEEL_DIR}"
WHEEL_PATH="$(ls -1t "${WHEEL_DIR}"/zpe_imc_kernel-*.whl | head -n 1)"
"${PYTHON_BIN}" -m pip install --force-reinstall --no-deps "${WHEEL_PATH}"

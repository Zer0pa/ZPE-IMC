#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${ROOT_DIR}/../../.." && pwd)"
DEFAULT_PYTHON="${REPO_ROOT}/.venv/bin/python"
PYTHON_BIN="${PYTHON_BIN:-${DEFAULT_PYTHON}}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

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

WHEEL_DIR="${ROOT_DIR}/target/wheels/${TARGET_TRIPLE}/pgo"
PROFILE_ROOT="${ROOT_DIR}/target/pgo/${TARGET_TRIPLE}"
RAW_DIR="${PROFILE_ROOT}/raw"
MERGED_PROFDATA="${PROFILE_ROOT}/merged.profdata"

rm -rf "${PROFILE_ROOT}" "${WHEEL_DIR}"
mkdir -p "${RAW_DIR}" "${WHEEL_DIR}"

"${PYTHON_BIN}" -m pip install --disable-pip-version-check --quiet maturin
rustup target add "${TARGET_TRIPLE}" >/dev/null 2>&1 || true

cd "${ROOT_DIR}"

RUSTFLAGS="-Cprofile-generate=${RAW_DIR}" \
  "${PYTHON_BIN}" -m maturin develop --release --manifest-path "${ROOT_DIR}/Cargo.toml" --target "${TARGET_TRIPLE}"

PYTHONPATH="${REPO_ROOT}/code:${REPO_ROOT}/executable" "${PYTHON_BIN}" - <<'PY'
from zpe_multimodal import IMCDecoder
from zpe_multimodal.canonical_demo import build_canonical_demo_stream

for _ in range(120):
    stream = build_canonical_demo_stream(require_env=False)
    IMCDecoder().decode(stream)
PY

if command -v xcrun >/dev/null 2>&1; then
  LLVM_PROFDATA="$(xcrun --find llvm-profdata || true)"
else
  LLVM_PROFDATA="$(command -v llvm-profdata || true)"
fi

if [[ -z "${LLVM_PROFDATA}" ]]; then
  echo "llvm-profdata not found" >&2
  exit 1
fi

"${LLVM_PROFDATA}" merge -o "${MERGED_PROFDATA}" "${RAW_DIR}"/*.profraw

RUSTFLAGS="-Cprofile-use=${MERGED_PROFDATA} -Cllvm-args=-pgo-warn-missing-function" \
  "${PYTHON_BIN}" -m maturin build --release --manifest-path "${ROOT_DIR}/Cargo.toml" --interpreter "${PYTHON_BIN}" --target "${TARGET_TRIPLE}" --out "${WHEEL_DIR}"

WHEEL_PATH="$(ls -1t "${WHEEL_DIR}"/zpe_imc_kernel-*.whl | head -n 1)"
"${PYTHON_BIN}" -m pip install --force-reinstall --no-deps "${WHEEL_PATH}"

if command -v llvm-bolt >/dev/null 2>&1; then
  echo "llvm-bolt detected at $(command -v llvm-bolt); post-link wheel patching is not automated in this script." >&2
fi

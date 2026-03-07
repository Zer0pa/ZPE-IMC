from __future__ import annotations

import json
import shutil
import subprocess
import unicodedata
from pathlib import Path

import pytest

from zpe_multimodal import decode as py_decode
from zpe_multimodal import encode as py_encode


ROOT = Path(__file__).resolve().parents[1]
WASM_DIR = ROOT / "wasm"
CONTRACT_SCRIPT = WASM_DIR / "scripts" / "run_contract.mjs"

SCENARIOS = [
    "hello world",
    "line1\nline2",
    "ASCII symbols !@#$%^&*()[]{}",
    "Cafe\u0301",
    "naive facade cooperate",
    "emoji 🙂🚀🔥",
    "math alpha beta gamma",
    "tabs\tand spaces",
    "mixed accents: deja vu",
    "quotes 'single' and \"double\"",
]


def _tooling_available() -> bool:
    required = ("node", "npm", "wasm-pack", "cargo", "rustc")
    return all(shutil.which(tool) for tool in required)


pytestmark = pytest.mark.skipif(
    not _tooling_available(),
    reason="WASM toolchain not available (node/npm/wasm-pack/cargo/rustc required)",
)


def _run_contract(scenarios: list[str]) -> dict:
    payload = json.dumps({"scenarios": scenarios})
    result = subprocess.run(
        ["node", str(CONTRACT_SCRIPT)],
        cwd=WASM_DIR,
        input=payload,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_wasm_interface_contract() -> None:
    subprocess.run(
        ["npm", "run", "build"],
        cwd=WASM_DIR,
        check=True,
        capture_output=True,
        text=True,
    )

    data = _run_contract(SCENARIOS)
    assert data["scenario_count"] == len(SCENARIOS)
    assert data["mismatch_count"] == 0

    for item in data["results"]:
        source = item["text"]
        ids = item["ids"]
        decoded = item["decoded"]
        expected = unicodedata.normalize("NFC", source)

        assert decoded == expected
        assert py_decode(ids) == expected
        assert py_decode(py_encode(source)) == expected

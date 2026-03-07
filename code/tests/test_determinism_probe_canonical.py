from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from tests.common import configure_env

configure_env()


V0_ROOT = Path(__file__).resolve().parents[2]
PROBE_SCRIPT = V0_ROOT / "executable" / "determinism_probe.py"


def test_canonical_determinism_probe_cli_stable() -> None:
    proc = subprocess.run(
        [sys.executable, str(PROBE_SCRIPT), "--runs", "5"],
        cwd=V0_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(proc.stdout.strip())
    assert payload["probe_id"] == "IMC_CANONICAL_DETERMINISM_PROBE_V1"
    assert payload["runs"] == 5
    assert payload["stable"] is True
    assert len(payload["hashes"]) == 5
    assert len(set(payload["hashes"])) == 1
    assert payload["canonical_hash"] == payload["hashes"][0]


def test_canonical_determinism_probe_out_file(tmp_path: Path) -> None:
    out_file = tmp_path / "probe.json"
    proc = subprocess.run(
        [sys.executable, str(PROBE_SCRIPT), "--runs", "3", "--out", str(out_file)],
        cwd=V0_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    from_stdout = json.loads(proc.stdout.strip())
    from_file = json.loads(out_file.read_text(encoding="utf-8"))
    assert from_stdout["probe_id"] == from_file["probe_id"]
    assert from_stdout["canonical_hash"] == from_file["canonical_hash"]
    assert from_file["stable"] is True

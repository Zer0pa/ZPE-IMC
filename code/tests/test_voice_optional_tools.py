from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from tests.common import configure_env

configure_env()


V0_ROOT = Path(__file__).resolve().parents[2]
TOOLS_SCRIPT = V0_ROOT / "executable" / "voice_groundtruth_optional_tools.py"


def _last_json_line(text: str) -> dict:
    lines = [line for line in text.splitlines() if line.strip()]
    return json.loads(lines[-1])


def test_voice_optional_tools_smoke_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(TOOLS_SCRIPT), "smoke", "--json"],
        cwd=V0_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = _last_json_line(proc.stdout)
    assert payload["status"] == "PASS"
    assert payload["alignment_segment_count"] >= 2
    assert payload["fallback_mode"] == "deterministic_fallback"


def test_voice_optional_tools_manifest_validate(tmp_path: Path) -> None:
    manifest = {
        "records": [
            {
                "utt_id": "utt-001",
                "audio_path": str((V0_ROOT / "code" / "fixtures" / "test.wav").resolve()),
                "text": "hello world",
            }
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(TOOLS_SCRIPT), "manifest-validate", "--manifest", str(manifest_path)],
        cwd=V0_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = _last_json_line(proc.stdout)
    assert payload["status"] == "PASS"
    assert payload["record_count"] == 1
    assert payload["malformed_records"] == 0

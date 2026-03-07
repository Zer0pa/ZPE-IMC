from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
V0_ROOT = ROOT.parent
VENV_PYTHON = V0_ROOT / ".venv" / "bin" / "python"


def _run_example(name: str) -> dict[str, object]:
    env = os.environ.copy()
    env.setdefault("PYTHONHASHSEED", "0")
    env.setdefault("STROKEGRAM_ENABLE_DIAGRAM", "1")
    env.setdefault("STROKEGRAM_ENABLE_MUSIC", "1")
    env.setdefault("STROKEGRAM_ENABLE_VOICE", "1")
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(ROOT) if not pythonpath else f"{ROOT}:{pythonpath}"
    runner = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    proc = subprocess.run(
        [runner, str(EXAMPLES / name)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout.strip())


def test_quickstart_smoke_deterministic() -> None:
    one = _run_example("quickstart.py")
    two = _run_example("quickstart.py")
    assert one == two
    assert one["example"] == "quickstart"
    assert one["roundtrip_ok"] is True
    assert one["decoded"] == one["text"]
    assert one["decoded2"] == one["text"]


def test_single_modality_text_smoke_deterministic() -> None:
    one = _run_example("single_modality_text.py")
    two = _run_example("single_modality_text.py")
    assert one["canonical_hash"] == two["canonical_hash"]
    assert one["example"] == "single_modality_text"
    assert one["stream_valid"] is True
    counts = one["modality_counts"]
    assert int(counts["text"]) > 0
    assert int(counts["diagram"]) == 0
    assert int(counts["music"]) == 0
    assert int(counts["voice"]) == 0
    assert int(counts["image"]) == 0
    assert int(counts["bpe"]) == 0


def test_multimodal_roundtrip_smoke_deterministic() -> None:
    one = _run_example("multimodal_roundtrip.py")
    two = _run_example("multimodal_roundtrip.py")
    assert one["canonical_hash"] == two["canonical_hash"]
    assert one["example"] == "multimodal_roundtrip"
    assert one["stream_valid"] is True
    assert one["decoded_contains_text"] is True
    counts = one["modality_counts"]
    assert int(counts["text"]) > 0
    assert int(counts["diagram"]) > 0
    assert int(counts["bpe"]) > 0

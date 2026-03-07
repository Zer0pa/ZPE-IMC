from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
V0_ROOT = ROOT.parent
DETERMINISM_PROBE_SCRIPT = V0_ROOT / "executable" / "determinism_probe.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import configure_env

configure_env()

from source.core.imc import IMCDecoder, IMCEncoder, iter_stream, stream_summary, validate_stream


def _random_dirty_word(rng: random.Random) -> Any:
    mode = rng.randrange(8)
    if mode == 0:
        return rng.randrange(0, 1 << 20)
    if mode == 1:
        return rng.randrange(-(1 << 20), 0)
    if mode == 2:
        return rng.randrange(1 << 20, 1 << 28)
    if mode == 3:
        return str(rng.randrange(0, 99999))
    if mode == 4:
        return None
    if mode == 5:
        return rng.random()
    if mode == 6:
        return {"bad": rng.randrange(0, 100)}
    return bool(rng.randrange(0, 2))


def test_wave1_dirty_stream_campaign_no_uncaught_crashes() -> None:
    rng = random.Random(20260220)
    decoder = IMCDecoder()
    cases = 1200

    for _ in range(cases):
        size = rng.randrange(0, 80)
        stream = [_random_dirty_word(rng) for _ in range(size)]

        result = decoder.decode(stream)
        summary = stream_summary(stream)
        valid, errors = validate_stream(stream)
        iterated = list(iter_stream(stream))

        assert isinstance(result.stream_valid, bool)
        assert isinstance(result.validation_errors, list)
        assert isinstance(summary["counts"], dict)
        assert isinstance(summary["ratios"], dict)
        assert isinstance(iterated, list)

        expected_keys = {"text", "diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste"}
        assert set(summary["counts"].keys()) == expected_keys
        assert set(result.modality_counts.keys()) == expected_keys

        if valid:
            assert errors == []


def _seeded_hash(seed: int) -> str:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    env["STROKEGRAM_ENABLE_DIAGRAM"] = "1"
    env["STROKEGRAM_ENABLE_MUSIC"] = "1"
    env["STROKEGRAM_ENABLE_VOICE"] = "1"
    env["PYTHONPATH"] = f"{ROOT}:{env.get('PYTHONPATH', '')}".rstrip(":")
    proc = subprocess.run(
        [sys.executable, str(DETERMINISM_PROBE_SCRIPT), "--runs", "1"],
        cwd=V0_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    payload = json.loads(proc.stdout.strip())
    assert payload["probe_id"] == "IMC_CANONICAL_DETERMINISM_PROBE_V1"
    return str(payload["canonical_hash"])


def test_wave1_determinism_replay_stable_across_hash_seeds() -> None:
    hashes = [_seeded_hash(seed) for seed in (0, 1, 7, 42, 99)]
    assert len(set(hashes)) == 1

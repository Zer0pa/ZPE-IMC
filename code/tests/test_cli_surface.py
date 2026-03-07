from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("STROKEGRAM_ENABLE_DIAGRAM", "1")
    env.setdefault("STROKEGRAM_ENABLE_MUSIC", "1")
    env.setdefault("STROKEGRAM_ENABLE_VOICE", "1")
    return subprocess.run(
        [sys.executable, "-m", "zpe_multimodal.cli", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )


def test_info_json_contract_fields() -> None:
    proc = _run_cli("info", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip())
    assert payload["command"] == "info"
    assert payload["imc_package_version"] == "3.0.0"
    assert "word_layout" in payload
    assert "modality_markers" in payload


def test_validate_json_rejects_dirty_words_without_crashing() -> None:
    proc = _run_cli("validate", "--json", "--stream-json", '[1, "bad", -5, 2000000]')
    assert proc.returncode == 1
    payload = json.loads(proc.stdout.strip())
    assert payload["command"] == "validate"
    assert payload["status"] == "FAIL"
    assert payload["stream_valid"] is False
    assert payload["total_words"] == 1
    assert isinstance(payload["validation_errors"], list)
    assert payload["validation_errors"]


def test_demo_json_is_stable_and_multimodal() -> None:
    proc = _run_cli("demo", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip())
    assert payload["command"] == "demo"
    assert payload["status"] == "PASS"
    counts = payload["modality_counts"]
    for key in ("text", "diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste"):
        assert counts[key] > 0


def test_public_api_contract_roundtrip() -> None:
    import zpe_multimodal as zm

    sample = "zpe contract 🙂"
    ids = zm.encode(sample)
    assert isinstance(ids, list)
    assert all(isinstance(word, int) for word in ids)
    assert zm.decode(ids) == sample
    assert zm.decode(tuple(ids)) == sample

    tok = zm.ZPETokenizer()
    assert tok.encode(sample) == ids
    assert tok.decode(ids) == sample


def test_tokenizer_from_lattice_accepts_existing_file(tmp_path: Path) -> None:
    import zpe_multimodal as zm

    lattice = tmp_path / "toy_lattice.json"
    lattice.write_text('{"name":"toy"}', encoding="utf-8")

    tok = zm.ZPETokenizer.from_lattice(str(lattice))
    assert tok.lattice_path == str(lattice.resolve())
    assert tok.decode(tok.encode("zpe")) == "zpe"


def test_tokenizer_from_lattice_rejects_missing_file() -> None:
    import zpe_multimodal as zm

    with pytest.raises(FileNotFoundError):
        zm.ZPETokenizer.from_lattice("/tmp/does-not-exist.zpe")

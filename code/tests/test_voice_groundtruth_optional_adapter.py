from __future__ import annotations

import json
from pathlib import Path
import sys
import types

import numpy as np

from tests.common import configure_env

configure_env()

import source.core.imc as _imc  # noqa: F401
from source.voice.audio import audio_to_strokes_with_metadata, load_alignment
from source.voice.text_to_phonemes import phoneme_tokens_with_mode


def test_load_alignment_parses_phone_tier_json(tmp_path: Path) -> None:
    payload = {
        "tiers": {
            "phones": {
                "entries": [
                    [0.0, 0.1, "DH"],
                    [0.1, 0.2, "AH0"],
                    [0.2, 0.3, "SIL"],
                    [0.3, 0.5, "K"],
                ]
            }
        }
    }
    path = tmp_path / "mfa_like.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    segments = load_alignment(path)
    assert [s["phone"] for s in segments] == ["DH", "AH0", "K"]
    assert all(float(s["end"]) > float(s["start"]) for s in segments)


def test_mode_dispatch_allows_deterministic_fallback_only() -> None:
    tokens, mode = phoneme_tokens_with_mode("Fallback check", preferred_modes=("deterministic_fallback",))
    assert mode == "deterministic_fallback"
    assert tokens


def test_audio_to_strokes_prefers_ground_truth_alignment(tmp_path: Path, monkeypatch) -> None:
    alignment = {
        "phones": [
            {"phone": "DH", "start": 0.0, "end": 0.09},
            {"phone": "AH0", "start": 0.09, "end": 0.18},
            {"phone": "K", "start": 0.18, "end": 0.28},
        ]
    }
    alignment_path = tmp_path / "alignment.json"
    alignment_path.write_text(json.dumps(alignment), encoding="utf-8")

    fake_librosa = types.SimpleNamespace(
        yin=lambda y, fmin, fmax, sr: np.linspace(120.0, 180.0, num=max(8, len(y)), dtype=np.float64)
    )
    monkeypatch.setitem(sys.modules, "librosa", fake_librosa)

    def _fake_loader(audio_path: str):
        return np.linspace(-1.0, 1.0, 1600, dtype=np.float32), 16000, "soundfile"

    monkeypatch.setattr("source.voice.audio.load_audio_mono_with_backend", _fake_loader)

    payload = audio_to_strokes_with_metadata(
        audio_path="fake.wav",
        transcript="the quick",
        alignment_path=str(alignment_path),
        time_step_sec=0.03,
    )
    assert payload["source_mode"] == "ground_truth_alignment"
    assert payload["alignment_segment_count"] == 3
    assert payload["phoneme_count"] == 3
    assert payload["audio_backend"] == "soundfile"
    assert len(payload["strokes"]) == 3

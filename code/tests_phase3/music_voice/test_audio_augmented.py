from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.diagram.quantize import DrawDir, MoveTo
from source.music.pack import MUSIC_TYPE_BIT, pack_music_strokes, unpack_music_words
from source.music.types import MusicStroke
from source.voice.pack import VOICE_TYPE_BIT, pack_voice_strokes, unpack_voice_words
from source.voice.prosody import augmented_js, descriptor_distance
from source.voice.types import VoiceStroke


def test_voice_speaker_dimensions_roundtrip() -> None:
    strokes = [
        VoiceStroke(
            commands=[MoveTo(40, 90), DrawDir(0), DrawDir(1)],
            symbol="AA",
            time_anchor_tick=40,
            formant_f1_band=5,
            formant_f2_band=12,
            speaking_rate_bucket=9,
            emotion_valence=3,
        )
    ]
    words = pack_voice_strokes(strokes)
    recovered = unpack_voice_words(words)
    assert len(recovered) == 1
    got = recovered[0]
    assert got.time_anchor_tick == 40
    assert got.formant_f1_band == 5
    assert got.formant_f2_band == 12
    assert got.speaking_rate_bucket == 9
    assert got.emotion_valence == 3


def test_music_time_anchor_roundtrip() -> None:
    stroke = MusicStroke(commands=[MoveTo(16, 60), DrawDir(0), DrawDir(0)], time_anchor_tick=16, track_id=1)
    words = pack_music_strokes([stroke])
    _meta, recovered = unpack_music_words(words)
    assert len(recovered) == 1
    assert recovered[0].time_anchor_tick == 16


def test_clone_and_wobbly_ruler_audio() -> None:
    a = pack_voice_strokes([VoiceStroke(commands=[MoveTo(5, 80), DrawDir(0)], symbol="AA", formant_f1_band=2)])
    b = pack_voice_strokes([VoiceStroke(commands=[MoveTo(5, 80), DrawDir(0)], symbol="AA", formant_f1_band=10)])
    assert a != b
    assert a == pack_voice_strokes([VoiceStroke(commands=[MoveTo(5, 80), DrawDir(0)], symbol="AA", formant_f1_band=2)])


def test_augmented_js_metric_nontrivial() -> None:
    delta = descriptor_distance(3, 10, 6, 0, 12, 2, 14, 7)
    score = augmented_js(0.025, delta)
    assert delta > 0.0
    assert score > 0.1


def test_dirty_control_tag_rejected() -> None:
    # Unknown control tag 7 in SUBTYPE_MOVE_T control payload.
    bad = (2 << 18) | (0 << 16) | (VOICE_TYPE_BIT | (1 << 10) | (7 << 7) | 1)
    with pytest.raises(ValueError):
        unpack_voice_words([bad])

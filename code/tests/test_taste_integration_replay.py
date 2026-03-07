from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import configure_env

configure_env()

from source.canonical_demo import CANONICAL_DEMO_TEXT, build_canonical_demo_stream, load_promoted_taste_events
from source.core.imc import IMCDecoder, IMCEncoder
from source.taste.codec import encode_taste_events


def test_promoted_taste_fixture_integrates_with_non_zero_count() -> None:
    events = load_promoted_taste_events()
    stream = IMCEncoder(require_env=False).add_taste_events(events).build()
    result = IMCDecoder().decode(stream)

    assert len(stream) > 0
    assert result.modality_counts["taste"] > 0
    assert result.modality_counts["image"] == 0
    assert len(result.taste_blocks) == 1
    assert len(result.taste_blocks[0][1]) == len(events)
    assert any(event.flavor_payload for event in result.taste_blocks[0][1])


def test_canonical_multimodal_replay_includes_promoted_taste_without_breaking_existing_modalities() -> None:
    stream = build_canonical_demo_stream(require_env=False)
    result = IMCDecoder().decode(stream)

    for key in ("text", "diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste"):
        assert result.modality_counts[key] > 0

    assert result.stream_valid
    assert len(result.taste_blocks) == 1
    assert len(result.taste_blocks[0][1]) == len(load_promoted_taste_events())
    assert any(event.flavor_payload for event in result.taste_blocks[0][1])


def test_canonical_multimodal_replay_text_emoji_roundtrips_exactly() -> None:
    stream = build_canonical_demo_stream(require_env=False)
    result = IMCDecoder().decode(stream)

    assert result.text == CANONICAL_DEMO_TEXT


def test_canonical_multimodal_replay_music_time_anchors_survive_roundtrip() -> None:
    stream = build_canonical_demo_stream(require_env=False)
    result = IMCDecoder().decode(stream)

    assert len(result.music_blocks) == 1
    _music_meta, music_out = result.music_blocks[0]
    music_start_ticks = [int(stroke.commands[0].x) for stroke in music_out]
    assert music_start_ticks == list(range(len(music_out)))
    assert [stroke.time_anchor_tick for stroke in music_out] == music_start_ticks


def test_promoted_taste_word_count_matches_fixture_encoding() -> None:
    events = load_promoted_taste_events()
    expected_word_count = len(encode_taste_events(events))

    stream = IMCEncoder(require_env=False).add_taste_events(events).build()
    assert len(stream) == expected_word_count

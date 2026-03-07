from __future__ import annotations

import numpy as np

from tests.common import FIXTURES, configure_env

from source.canonical_demo import (
    CANONICAL_DEMO_SVG,
    build_promoted_mental_entries,
    build_promoted_smell_records,
    build_promoted_touch_anchor,
    build_promoted_touch_frame,
    build_promoted_voice_strokes,
    load_promoted_taste_events,
)
from source.core.imc import IMCDecoder, IMCEncoder, _classify_word, stream_stats, validate_stream
from source.diagram.pack import DIAGRAM_TYPE_BIT
from source.image.quadtree_enhanced_codec import IMAGE_FAMILY_MASK, IMAGE_FAMILY_VALUE
from source.mental.pack import MENTAL_TYPE_BIT
from source.music.pack import MUSIC_TYPE_BIT
from source.smell.pack import SMELL_TYPE_BIT
from source.taste.pack import TASTE_TYPE_BIT
from source.touch.pack import TOUCH_TYPE_BIT
from source.voice.pack import VOICE_TYPE_BIT

BPE_TYPE_BIT = 0x1000


def build_image() -> np.ndarray:
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    img[:, :, 0] = np.tile(np.linspace(0, 255, 8, dtype=np.uint8), (8, 1))
    img[:, :, 1] = np.tile(np.linspace(255, 0, 8, dtype=np.uint8), (8, 1)).T
    img[:, :, 2] = 128
    return img


def type_exclusive(words: list[int]) -> bool:
    for word in words:
        mode = (int(word) >> 18) & 0x3
        version = (int(word) >> 16) & 0x3
        payload = int(word) & 0xFFFF

        if mode == 3:
            if _classify_word(int(word)) != "mental":
                return False
            continue

        if mode != 2:
            continue

        is_image = (payload & IMAGE_FAMILY_MASK) == IMAGE_FAMILY_VALUE
        matches = []
        if payload & DIAGRAM_TYPE_BIT:
            matches.append("diagram")
        if payload & MUSIC_TYPE_BIT:
            matches.append("music")
        if payload & VOICE_TYPE_BIT:
            matches.append("voice")
        if payload & BPE_TYPE_BIT:
            matches.append("bpe")
        if (payload & TOUCH_TYPE_BIT) and not is_image:
            matches.append("touch")
        if (payload & SMELL_TYPE_BIT) and not is_image and not (payload & TOUCH_TYPE_BIT):
            matches.append("smell")
        if (payload & MENTAL_TYPE_BIT) and not is_image and not (payload & (TOUCH_TYPE_BIT | SMELL_TYPE_BIT)):
            matches.append("mental")
        if (payload & TASTE_TYPE_BIT) and version in (1, 2, 3):
            matches.append("taste")
        if is_image:
            matches.append("image")

        expected = _classify_word(int(word))
        if matches and expected not in matches:
            return False
    return True


def _decoded_stroke_count(blocks: list[tuple[object, list[object]]]) -> int:
    return sum(len(strokes) for _, strokes in blocks)


def test_all_modality_stream() -> None:
    configure_env()

    text_in = "The complete ZPE multimodal codec. 🙂"
    voice_in, voice_meta = build_promoted_voice_strokes()
    mental_in = build_promoted_mental_entries()
    touch_frame_in, touch_frame_meta = build_promoted_touch_frame()
    touch_anchor_in, touch_anchor_meta = build_promoted_touch_anchor()
    smell_in, smell_meta = build_promoted_smell_records()
    taste_in = load_promoted_taste_events()

    stream = (
        IMCEncoder()
        .add_text(text_in)
        .add_svg(CANONICAL_DEMO_SVG)
        .add_music(FIXTURES / "simple_scale.musicxml")
        .add_voice(voice_in, metadata=voice_meta)
        .add_image(build_image(), bits=3)
        .add_bpe([100, 200, 300])
        .add_mental(mental_in)
        .add_touch(touch_frame_in, metadata=touch_frame_meta)
        .add_smell(smell_in, metadata=smell_meta)
        .add_touch(touch_anchor_in, metadata=touch_anchor_meta)
        .add_taste_events(taste_in)
        .build()
    )

    result = IMCDecoder().decode(stream)
    valid, errors = validate_stream(stream)
    stats = stream_stats(stream)

    assert valid and errors == []
    assert result.stream_valid
    assert result.text == text_in

    for key in ("text", "diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste"):
        assert result.modality_counts[key] > 0, key

    assert len(result.diagram_blocks) == 1
    assert result.diagram_blocks[0][0].stroke == "#00ffff"
    assert result.diagram_blocks[0][0].stroke_width is not None

    music_meta, music_out = result.music_blocks[0]
    assert music_meta is not None
    music_start_ticks = [int(stroke.commands[0].x) for stroke in music_out]
    assert music_start_ticks == list(range(len(music_out)))
    assert [stroke.time_anchor_tick for stroke in music_out] == music_start_ticks

    assert len(result.voice_blocks) == 1
    voice_out = result.voice_blocks[0]
    assert [stroke.time_anchor_tick for stroke in voice_out] == [stroke.time_anchor_tick for stroke in voice_in]
    assert [stroke.formant_f1_band for stroke in voice_out] == [stroke.formant_f1_band for stroke in voice_in]
    assert [stroke.formant_f2_band for stroke in voice_out] == [stroke.formant_f2_band for stroke in voice_in]
    assert [stroke.speaking_rate_bucket for stroke in voice_out] == [stroke.speaking_rate_bucket for stroke in voice_in]
    assert [stroke.emotion_valence for stroke in voice_out] == [stroke.emotion_valence for stroke in voice_in]

    mental_meta, mental_out = result.mental_blocks[0]
    assert mental_meta is not None
    assert len(mental_out) == len(mental_in)
    assert any(int(stroke.direction_profile) == 1 for stroke in mental_out)

    assert len(result.touch_blocks) == 2
    touch_count = _decoded_stroke_count(result.touch_blocks)
    assert touch_count == len(touch_frame_in) + len(touch_anchor_in)

    touch_frame_out_meta, _touch_frame_out = result.touch_blocks[0]
    assert touch_frame_out_meta is not None
    assert touch_frame_out_meta["timed_frame"]["cooccurrence_preserved"]
    assert touch_frame_out_meta["z_layers"]["surface"] == [0, 1, 2]
    assert touch_frame_out_meta["z_layers"]["dermal"] == [2, 3, 4]

    touch_anchor_out_meta, _touch_anchor_out = result.touch_blocks[1]
    assert touch_anchor_out_meta is not None
    assert touch_anchor_out_meta["anchored_touch"]["anchor"] == (4, 1)
    assert len(touch_anchor_out_meta["raii_complete"]) == 1
    assert len(touch_anchor_out_meta["raii_frequency_samples"]) == 3

    smell_out_meta, smell_out = result.smell_blocks[0]
    assert smell_out_meta is not None
    assert smell_out_meta["z_level"] == "episodic"
    assert smell_out_meta["adaptation"] == {"half_life": 6, "floor": 3}
    assert len(smell_out) == len(smell_in)
    assert len(smell_out_meta["augmented_records"]) == len(smell_in)

    taste_out_meta, taste_out = result.taste_blocks[0]
    assert taste_out_meta is not None
    assert len(taste_out) == len(taste_in)
    assert any(event.flavor_payload for event in taste_out)

    assert type_exclusive(stream)
    assert 50 <= len(stream) <= 5000

    assert stats["counts"]["mental"] >= len(mental_out)
    assert stats["counts"]["touch"] >= touch_count
    assert stats["counts"]["smell"] >= len(smell_out)

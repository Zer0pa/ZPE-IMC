from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.core.constants import Mode
from source.core.imc import BPE_TYPE_BIT, IMCDecoder, IMCEncoder, _classify_word
from source.diagram.pack import DIAGRAM_TYPE_BIT
from source.image.quadtree_enhanced_codec import IMAGE_FAMILY_MASK, IMAGE_FAMILY_VALUE
from source.mental.pack import MENTAL_TYPE_BIT
from source.music.pack import MUSIC_TYPE_BIT
from source.smell.pack import SMELL_TYPE_BIT
from source.taste.pack import TASTE_TYPE_BIT
from source.touch.pack import TOUCH_TYPE_BIT
from source.voice.pack import VOICE_TYPE_BIT


def _word(mode: int, payload: int, *, version: int = 0) -> int:
    return ((int(mode) & 0x3) << 18) | ((int(version) & 0x3) << 16) | (int(payload) & 0xFFFF)


def test_touch_bit_plus_image_marker_collision_word() -> None:
    payload = TOUCH_TYPE_BIT | IMAGE_FAMILY_VALUE
    # Enhanced family marker requires bits [11:10] == 0b01.
    # This collision payload is 0b11 in [11:10], so it should stay touch.
    assert (payload & IMAGE_FAMILY_MASK) != IMAGE_FAMILY_VALUE
    assert _classify_word(_word(Mode.EXTENSION.value, payload)) == "touch"


def test_touch_without_image_marker_dispatches_touch() -> None:
    payload = TOUCH_TYPE_BIT | 0x0012
    assert _classify_word(_word(Mode.EXTENSION.value, payload)) == "touch"


def test_smell_bit_with_image_marker_prefers_image() -> None:
    payload = SMELL_TYPE_BIT | IMAGE_FAMILY_VALUE
    assert (payload & IMAGE_FAMILY_MASK) == IMAGE_FAMILY_VALUE
    assert _classify_word(_word(Mode.EXTENSION.value, payload)) == "image"


def test_mental_bit_mode2_with_image_marker_prefers_image() -> None:
    payload = MENTAL_TYPE_BIT | IMAGE_FAMILY_VALUE
    assert (payload & IMAGE_FAMILY_MASK) == IMAGE_FAMILY_VALUE
    assert _classify_word(_word(Mode.EXTENSION.value, payload)) == "image"


def test_mental_mode3_dispatches_mental() -> None:
    payload = MENTAL_TYPE_BIT | 0x0033
    assert _classify_word(_word(Mode.RESERVED.value, payload)) == "mental"


def test_mode2_without_type_bits_dispatches_text() -> None:
    assert _classify_word(_word(Mode.EXTENSION.value, 0)) == "text"


def test_single_modality_dispatch_baselines() -> None:
    cases = {
        "diagram": DIAGRAM_TYPE_BIT,
        "music": MUSIC_TYPE_BIT,
        "voice": VOICE_TYPE_BIT,
        "bpe": BPE_TYPE_BIT,
        "touch": TOUCH_TYPE_BIT,
        "smell": SMELL_TYPE_BIT,
        "mental": MENTAL_TYPE_BIT,
        "image": IMAGE_FAMILY_VALUE,
        "text": 0,
    }
    for expected, payload in cases.items():
        assert _classify_word(_word(Mode.EXTENSION.value, payload)) == expected


def test_dense_edge_payload_is_deterministic() -> None:
    # Edge payload with many high bits set should still dispatch deterministically.
    dense_payload = 0xFFFF
    assert _classify_word(_word(Mode.EXTENSION.value, dense_payload)) == "music"


def test_isolated_versioned_taste_word_does_not_claim_taste() -> None:
    payload = TASTE_TYPE_BIT | 0x0031
    assert _classify_word(_word(Mode.EXTENSION.value, payload, version=1)) == "image"


def test_taste_sequence_routes_taste_not_image() -> None:
    # v0/v1/v2 taste sequence must be consumed by taste lane even though 0x0400
    # overlaps the enhanced image family marker.
    words = [
        _word(Mode.EXTENSION.value, TASTE_TYPE_BIT | 0x0019, version=0),
        _word(Mode.EXTENSION.value, TASTE_TYPE_BIT | 0x0030, version=1),
        _word(Mode.EXTENSION.value, TASTE_TYPE_BIT | 0x003F, version=2),
    ]
    result = IMCDecoder().decode(words)
    assert result.modality_counts["taste"] == 3
    assert result.modality_counts["image"] == 0
    assert len(result.taste_blocks) == 1
    assert len(result.taste_blocks[0][1]) == 1


def test_malformed_int_dirty_word_is_structured_not_crash() -> None:
    stream = IMCEncoder(require_env=False).add_text("dirty data robustness").add_bpe([12, 34]).build()
    stream.insert(1, 0)  # in-range int that can trigger unknown-unit decode failures
    result = IMCDecoder().decode(stream)
    assert result.stream_valid is False
    assert any("text_decode_error" in err for err in result.validation_errors)

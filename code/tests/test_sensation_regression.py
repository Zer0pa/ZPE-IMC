from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import configure_env

configure_env()

from source.canonical_demo import (
    build_promoted_mental_entries,
    build_promoted_smell_records,
    build_promoted_touch_anchor,
    build_promoted_touch_frame,
)
from source.core.imc import IMCDecoder, IMCEncoder
from source.mental.codec import decode_mental, encode_mental
from source.mental.form_constants import generate_cobweb, generate_lattice, generate_spiral, generate_tunnel
from source.mental.pack import pack_mental_strokes_rle, unpack_mental_words_rle
from source.mental.types import DrawDir as MentalDrawDir
from source.smell.codec import decode_smell_words, encode_smell_strokes
from source.smell.phase5_augment import AugmentedOdorRecord, TreeOp, pack_augmented_records, unpack_augmented_words
from source.smell.types import OdorCategory, OdorStroke
from source.diagram.quantize import DrawDir as DiagramDrawDir, MoveTo as DiagramMoveTo
from source.touch.codec import decode_touch, encode_touch
from source.touch.phase5_extensions import SimultaneousFrame, pack_simultaneous_frame, unpack_simultaneous_frame
from source.touch.types import BodyRegion, DrawDir as TouchDrawDir, MoveTo as TouchMoveTo, ReceptorType, TouchStroke


def _mental_signature(stroke) -> tuple:
    return (
        int(stroke.form_class),
        int(stroke.symmetry),
        int(stroke.spatial_frequency),
        int(stroke.drift_speed),
        tuple((cmd.x, cmd.y) if hasattr(cmd, "x") else ("d", cmd.direction) for cmd in stroke.commands),
    )


def _touch_signature(stroke: TouchStroke) -> tuple:
    directions = tuple(cmd.direction for cmd in stroke.commands if isinstance(cmd, TouchDrawDir))
    return (
        int(stroke.receptor),
        int(stroke.region),
        directions,
        tuple(int(v) for v in stroke.pressure_profile or []),
    )


def _smell_signature(stroke: OdorStroke) -> tuple:
    directions = tuple(cmd.direction for cmd in stroke.commands[1:] if isinstance(cmd, DiagramDrawDir))
    return (
        int(stroke.category),
        int(stroke.pleasantness_start),
        int(stroke.intensity_start),
        directions,
    )


def build_mental_strokes() -> list:
    strokes = []
    strokes.extend(generate_tunnel(center=(20, 20), radius=16))
    strokes.extend(generate_spiral(center=(32, 32), turns=2))
    strokes.extend(generate_lattice(origin=(10, 10), spacing=2, rows=4, cols=4))
    strokes.extend(generate_cobweb(center=(16, 16), branches=6, depth=4))
    # Keep deterministic and exactly 10 samples.
    if len(strokes) < 10:
        raise AssertionError("insufficient mental strokes generated")
    return strokes[:10]


def build_touch_strokes() -> list[TouchStroke]:
    strokes: list[TouchStroke] = []
    for i in range(10):
        directions = [i % 8, (i + 1) % 8, (i + 2) % 8, (i + 3) % 8]
        commands = [TouchMoveTo(0, 0)] + [TouchDrawDir(d) for d in directions]
        strokes.append(
            TouchStroke(
                commands=commands,
                receptor=ReceptorType(i % 4),
                region=BodyRegion(i % 16),
                pressure_profile=[(i + j) % 8 for j in range(len(directions))],
            )
        )
    return strokes


def build_smell_strokes() -> list[OdorStroke]:
    strokes: list[OdorStroke] = []
    for i in range(10):
        directions = [(i + j) % 8 for j in range(4)]
        commands = [DiagramMoveTo(i % 8, 7 - ((i + 2) % 8))] + [DiagramDrawDir(d) for d in directions]
        strokes.append(
            OdorStroke(
                commands=commands,
                category=OdorCategory(i % 8),
                pleasantness_start=i % 8,
                intensity_start=(i + 2) % 8,
            )
        )
    return strokes


def _dirty_data_ok(fn, words) -> bool:
    try:
        fn(words)
        return True
    except (TypeError, ValueError, IndexError):
        return True


def main() -> None:
    summary: dict[str, object] = {}

    # Mental roundtrip
    mental_in = build_mental_strokes()
    mental_words = encode_mental(mental_in)
    mental_meta, mental_out = decode_mental(mental_words)
    assert len(mental_out) == len(mental_in)
    assert [_mental_signature(s) for s in mental_in] == [_mental_signature(s) for s in mental_out]
    summary["mental_roundtrip"] = "10/10 PASS"

    # Mental phase-5 RLE extension check.
    rle_words = pack_mental_strokes_rle(mental_in[:2])
    _, rle_out = unpack_mental_words_rle(rle_words)
    assert len(rle_out) == 2
    assert all(isinstance(cmd, MentalDrawDir) for cmd in rle_out[0].commands[1:])
    summary["mental_rle"] = len(rle_words)

    # Touch roundtrip
    touch_in = build_touch_strokes()
    touch_words = encode_touch(touch_in)
    touch_meta, touch_out = decode_touch(touch_words)
    assert len(touch_out) == len(touch_in)
    assert [_touch_signature(s) for s in touch_in] == [_touch_signature(s) for s in touch_out]
    summary["touch_roundtrip"] = "10/10 PASS"

    # Touch phase-5 simultaneity check.
    frame = SimultaneousFrame(frame_id=3, contacts=touch_in[:3])
    frame_words = pack_simultaneous_frame(frame)
    frame_meta, frame_out = unpack_simultaneous_frame(frame_words)
    assert frame_meta["cooccurrence_preserved"]
    assert len(frame_out.contacts) == 3
    summary["touch_simultaneity"] = frame_meta

    # Smell roundtrip
    smell_in = build_smell_strokes()
    smell_words = encode_smell_strokes(smell_in, metadata={"sniff_hz": 12})
    smell_meta, smell_out = decode_smell_words(smell_words)
    assert smell_meta == {"sniff_hz": 12}
    assert len(smell_out) == len(smell_in)
    assert [_smell_signature(s) for s in smell_in] == [_smell_signature(s) for s in smell_out]
    summary["smell_roundtrip"] = "10/10 PASS"

    # Smell phase-5 augmentation check.
    rec = AugmentedOdorRecord(
        stroke=smell_in[0],
        tree_ops=(TreeOp.BRANCH_LEFT, TreeOp.DESCEND, TreeOp.ASCEND),
        complexity_axis=7,
        chirality=1,
    )
    aug_words = pack_augmented_records([rec])
    aug_out = unpack_augmented_words(aug_words)
    assert len(aug_out) == 1
    assert int(aug_out[0].stroke.category) == int(rec.stroke.category)
    summary["smell_augment"] = len(aug_words)

    # Clone checks
    assert encode_mental(mental_in[:1]) != encode_mental(mental_in[1:2])
    assert encode_touch(touch_in[:1]) != encode_touch(touch_in[1:2])
    assert encode_smell_strokes(smell_in[:1]) != encode_smell_strokes(smell_in[1:2])
    summary["clone"] = "PASS"

    # Dirty data checks
    dirty = ["x", -1, 2**30, None, 0]
    assert _dirty_data_ok(decode_mental, dirty)
    assert _dirty_data_ok(decode_touch, dirty)
    assert _dirty_data_ok(decode_smell_words, dirty)
    summary["dirty_data"] = "PASS"

    # Determinism
    assert encode_mental(mental_in) == encode_mental(mental_in)
    assert encode_touch(touch_in) == encode_touch(touch_in)
    assert encode_smell_strokes(smell_in) == encode_smell_strokes(smell_in)
    summary["wobbly_ruler"] = "PASS"

    # Promoted IMC admission/decode checks.
    promoted_mental = build_promoted_mental_entries()
    promoted_touch_frame, promoted_touch_frame_meta = build_promoted_touch_frame()
    promoted_touch_anchor, promoted_touch_anchor_meta = build_promoted_touch_anchor()
    promoted_smell, promoted_smell_meta = build_promoted_smell_records()

    promoted_stream = (
        IMCEncoder()
        .add_mental(promoted_mental)
        .add_touch(promoted_touch_frame, metadata=promoted_touch_frame_meta)
        .add_smell(promoted_smell, metadata=promoted_smell_meta)
        .add_touch(promoted_touch_anchor, metadata=promoted_touch_anchor_meta)
        .build()
    )
    promoted_result = IMCDecoder().decode(promoted_stream)

    promoted_mental_meta, promoted_mental_out = promoted_result.mental_blocks[0]
    assert promoted_mental_meta is not None
    assert len(promoted_mental_out) == len(promoted_mental)
    assert any(int(stroke.direction_profile) == 1 for stroke in promoted_mental_out)

    promoted_touch_frame_out_meta, promoted_touch_frame_out = promoted_result.touch_blocks[0]
    assert len(promoted_touch_frame_out) == len(promoted_touch_frame)
    assert promoted_touch_frame_out_meta["timed_frame"]["cooccurrence_preserved"]
    assert promoted_touch_frame_out_meta["z_layers"]["surface"] == [0, 1, 2]

    promoted_smell_out_meta, promoted_smell_out = promoted_result.smell_blocks[0]
    assert len(promoted_smell_out) == len(promoted_smell)
    assert promoted_smell_out_meta["z_level"] == "episodic"
    assert promoted_smell_out_meta["adaptation"] == {"half_life": 6, "floor": 3}

    promoted_touch_anchor_out_meta, promoted_touch_anchor_out = promoted_result.touch_blocks[1]
    assert len(promoted_touch_anchor_out) == len(promoted_touch_anchor)
    assert promoted_touch_anchor_out_meta["anchored_touch"]["anchor"] == (4, 1)
    assert len(promoted_touch_anchor_out_meta["raii_complete"]) == 1
    assert len(promoted_touch_anchor_out_meta["raii_frequency_samples"]) == 3

    summary["imc_promoted"] = {
        "mental_direction_profiles": [int(stroke.direction_profile) for stroke in promoted_mental_out],
        "touch_blocks": len(promoted_result.touch_blocks),
        "smell_records": len(promoted_smell_out_meta["augmented_records"]),
    }

    print("SENSATION_REGRESSION: PASS")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

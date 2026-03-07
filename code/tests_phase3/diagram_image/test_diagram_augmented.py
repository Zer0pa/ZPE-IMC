from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.diagram.pack import VISUAL_TYPE_BIT, pack_diagram_paths, unpack_diagram_words
from source.diagram.quantize import DrawDir, MoveTo, PolylineShape, StrokePath, polylines_to_strokes_liberated


def _styled_path() -> StrokePath:
    return StrokePath(
        commands=[MoveTo(12, 12), DrawDir(0), DrawDir(0), DrawDir(6)],
        stroke="#ff0000",
        stroke_width=3.0,
        dash="dash",
    )


def test_style_suffix_roundtrip() -> None:
    words = pack_diagram_paths([_styled_path()], encode_styles=True)
    decoded = unpack_diagram_words(words)
    assert len(decoded) == 1
    got = decoded[0]
    assert got.stroke == "#ff0000"
    assert got.stroke_width == 3.0
    assert got.dash == "dash"


def test_style_suffix_word_count_plus_three() -> None:
    plain = pack_diagram_paths([_styled_path()], encode_styles=False)
    styled = pack_diagram_paths([_styled_path()], encode_styles=True)
    assert len(styled) == len(plain) + 3


def test_liberated_construction_reanchors_segments() -> None:
    poly = PolylineShape(points=[(0, 0), (2, 0), (2, 2), (4, 2)], stroke="#000000", stroke_width=1.0)
    paths = polylines_to_strokes_liberated([poly])
    assert len(paths) == 1
    move_count = sum(1 for cmd in paths[0].commands if isinstance(cmd, MoveTo))
    assert move_count >= 3


def test_clone_and_wobbly_ruler() -> None:
    a = pack_diagram_paths([_styled_path()], encode_styles=True)
    b = pack_diagram_paths([
        StrokePath(commands=[MoveTo(12, 12), DrawDir(0), DrawDir(6)], stroke="#00ff00", stroke_width=1.0, dash="dot")
    ], encode_styles=True)
    assert a != b
    assert a == pack_diagram_paths([_styled_path()], encode_styles=True)


def test_dirty_style_suffix_graceful() -> None:
    words = pack_diagram_paths([_styled_path()], encode_styles=True)
    corrupted = list(words)
    # break expected suffix structure: mutate first suffix word subtype
    corrupted[-3] = (corrupted[-3] & ~0x6000) | VISUAL_TYPE_BIT | (3 << 13)
    decoded = unpack_diagram_words(corrupted)
    assert len(decoded) >= 1
    assert isinstance(decoded[0].commands[0], MoveTo)

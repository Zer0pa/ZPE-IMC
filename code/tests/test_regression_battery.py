from __future__ import annotations

import inspect
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import configure_env

configure_env()

from source.core.codec import decode, encode, encode_bpe_bridge
from source.diagram.pack import DIAGRAM_TYPE_BIT, pack_diagram_paths, unpack_diagram_words
from source.diagram.quantize import DrawDir, MoveTo, StrokePath, polylines_to_strokes, strokes_to_polylines
from source.diagram.svg_io import polylines_to_svg, svg_to_polylines
from source.music.pack import MUSIC_TYPE_BIT, pack_music_strokes, unpack_music_words
from source.music.types import MusicMetadata, MusicStroke
from source.voice.pack import VOICE_TYPE_BIT, pack_voice_strokes, unpack_voice_words
from source.voice.types import VoiceMetadata, VoiceStroke
from source.image.quadtree_codec import DIAGRAM_TYPE_BIT as IMAGE_TYPE_BIT
from source.image.quadtree_codec import psnr, quantize_rgb, quadtree_decode, quadtree_encode

BPE_TYPE_BIT = 0x1000


def assert_type_exclusive(word: int, bit: int) -> None:
    payload = word & 0xFFFF
    assert payload & bit, f"missing type bit {bit:#x} for word {word:#x}"
    others = [DIAGRAM_TYPE_BIT, MUSIC_TYPE_BIT, VOICE_TYPE_BIT, BPE_TYPE_BIT]
    for other in others:
        if other == bit:
            continue
        assert (payload & other) == 0, f"type bit collision in word {word:#x}: {bit:#x} with {other:#x}"


def main() -> None:
    summary: dict[str, object] = {}

    # Text
    text_cases = ["hello world", "cafe resume", "日本語", "!@#$%^&*()", ""]
    for case in text_cases:
        out = decode(encode(case))
        assert out == case, f"text mismatch for {case!r}: {out!r}"
    summary["text_roundtrip"] = "5/5 PASS"

    # Music
    music_stroke = MusicStroke(commands=[MoveTo(0, 60), DrawDir(0), DrawDir(0)])
    music_meta = MusicMetadata(time_signature=(4, 4), key_signature=0, tempo=120.0, dynamic_base=80)
    music_words = pack_music_strokes([music_stroke], metadata=music_meta)
    rec_meta, rec_music = unpack_music_words(music_words)
    assert len(rec_music) >= 1
    assert rec_meta is not None
    for w in music_words:
        assert_type_exclusive(w, MUSIC_TYPE_BIT)
    summary["music_words"] = len(music_words)

    # Voice
    voice_stroke = VoiceStroke(commands=[MoveTo(0, 100), DrawDir(0), DrawDir(1)], symbol="AA", stress=False)
    voice_meta = VoiceMetadata(language="en-us", time_step_sec=0.03, pitch_levels=8)
    voice_words = pack_voice_strokes([voice_stroke], metadata=voice_meta)
    rec_voice = unpack_voice_words(voice_words)
    assert len(rec_voice) >= 1
    for w in voice_words:
        assert_type_exclusive(w, VOICE_TYPE_BIT)
    summary["voice_words"] = len(voice_words)

    # Diagram
    diagram_path = StrokePath(commands=[MoveTo(10, 10), DrawDir(0), DrawDir(0), DrawDir(6), DrawDir(6)])
    diagram_words = pack_diagram_paths([diagram_path])
    rec_diagram = unpack_diagram_words(diagram_words)
    assert len(rec_diagram) >= 1
    for w in diagram_words:
        assert_type_exclusive(w, DIAGRAM_TYPE_BIT)
    summary["diagram_words"] = len(diagram_words)

    # SVG roundtrip
    svg_in = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<rect x="10" y="10" width="80" height="80"/></svg>'
    )
    polys = svg_to_polylines(svg_in)
    strokes = polylines_to_strokes(polys)
    polys2 = strokes_to_polylines(strokes)
    svg_out = polylines_to_svg(polys2)
    assert len(polys) > 0
    assert len(svg_out) > 0
    summary["svg_roundtrip"] = {"in_paths": len(polys), "out_len": len(svg_out)}

    # Image quadtree PSNR regression
    img = np.full((32, 32, 3), 128, dtype=np.uint8)
    img_words = quadtree_encode(img, bit_depth=3)
    img_rec = quadtree_decode(img_words, shape=(32, 32), bit_depth=3)
    img_ref = quantize_rgb(img, bit_depth=3)
    img_psnr = psnr(img_ref, img_rec)
    assert img_psnr >= 99.0
    for w in img_words:
        assert ((w >> 18) & 0x3) == 2
        assert (w & 0xFFFF) & IMAGE_TYPE_BIT
    summary["image_psnr_db"] = img_psnr

    # BPE bridge
    bpe_words = encode_bpe_bridge([100, 200, 4095])
    for w in bpe_words:
        mode = (w >> 18) & 0x3
        assert mode == 2
        assert_type_exclusive(w, BPE_TYPE_BIT)
    summary["bpe_words"] = len(bpe_words)

    # Clone tests
    assert encode("abc") != encode("xyz")
    assert music_words != voice_words
    summary["clone_checks"] = "PASS"

    # Determinism
    assert encode("determinism") == encode("determinism")
    assert pack_diagram_paths([diagram_path]) == pack_diagram_paths([diagram_path])
    summary["determinism"] = "PASS"

    # Dirty data / empty input handling
    assert decode(encode("")) == ""
    assert isinstance(pack_music_strokes([], metadata=MusicMetadata()), list)
    assert isinstance(pack_voice_strokes([], metadata=VoiceMetadata()), list)
    assert pack_diagram_paths([]) == []
    summary["dirty_data"] = "PASS"

    # Signature stability checks
    summary["signatures"] = {
        "pack_music_strokes": str(inspect.signature(pack_music_strokes)),
        "unpack_music_words": str(inspect.signature(unpack_music_words)),
        "pack_voice_strokes": str(inspect.signature(pack_voice_strokes)),
        "unpack_voice_words": str(inspect.signature(unpack_voice_words)),
        "pack_diagram_paths": str(inspect.signature(pack_diagram_paths)),
        "unpack_diagram_words": str(inspect.signature(unpack_diagram_words)),
    }

    print("REGRESSION_BATTERY: PASS")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

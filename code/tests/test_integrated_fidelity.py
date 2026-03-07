from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import FIXTURES, configure_env, flatten_points, mean_point_distance

configure_env()

from source.core.imc import IMCDecoder, IMCEncoder
from source.diagram.quantize import DrawDir as DiagramDrawDir, MoveTo as DiagramMoveTo
from source.diagram.quantize import strokes_to_polylines
from source.diagram.svg_io import svg_to_polylines
from source.image.quadtree_codec import psnr
from source.image.quadtree_enhanced_codec import decode_enhanced, encode_enhanced
from source.mental.form_constants import generate_lattice, generate_spiral, generate_tunnel
from source.music.parser import musicxml_to_events
from source.smell.types import OdorCategory, OdorStroke
from source.touch.types import BodyRegion, DrawDir as TouchDrawDir, MoveTo as TouchMoveTo, ReceptorType, TouchStroke


SVG_TRIANGLE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<polygon points="50,10 90,90 10,90"/></svg>'
)


def build_mental() -> list:
    return [
        generate_tunnel(center=(30, 30), radius=12)[0],
        generate_spiral(center=(30, 30), turns=2)[0],
        generate_lattice(origin=(8, 8), spacing=2, rows=3, cols=3)[0],
    ]


def build_touch() -> list[TouchStroke]:
    return [
        TouchStroke(
            commands=[TouchMoveTo(0, 0), TouchDrawDir(0), TouchDrawDir(1), TouchDrawDir(2)],
            receptor=ReceptorType.SA_I,
            region=BodyRegion.INDEX_TIP,
            pressure_profile=[2, 3, 4],
        ),
        TouchStroke(
            commands=[TouchMoveTo(0, 0), TouchDrawDir(4), TouchDrawDir(4), TouchDrawDir(4)],
            receptor=ReceptorType.RA_I,
            region=BodyRegion.PALM_CENTER,
            pressure_profile=[6, 6, 6],
        ),
        TouchStroke(
            commands=[TouchMoveTo(0, 0), TouchDrawDir(7), TouchDrawDir(6), TouchDrawDir(5)],
            receptor=ReceptorType.RA_II,
            region=BodyRegion.THUMB_TIP,
            pressure_profile=[3, 2, 1],
        ),
    ]


def build_smell() -> list[OdorStroke]:
    return [
        OdorStroke(
            commands=[DiagramMoveTo(5, 2), DiagramDrawDir(1), DiagramDrawDir(0), DiagramDrawDir(6)],
            category=OdorCategory.FLORAL,
            pleasantness_start=5,
            intensity_start=5,
        ),
        OdorStroke(
            commands=[DiagramMoveTo(6, 3), DiagramDrawDir(0), DiagramDrawDir(0), DiagramDrawDir(4)],
            category=OdorCategory.FRUITY,
            pleasantness_start=6,
            intensity_start=4,
        ),
        OdorStroke(
            commands=[DiagramMoveTo(3, 1), DiagramDrawDir(4), DiagramDrawDir(5), DiagramDrawDir(6)],
            category=OdorCategory.WOODY_EARTHY,
            pleasantness_start=3,
            intensity_start=6,
        ),
    ]


def build_image() -> np.ndarray:
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[:, :, 0] = np.tile(np.linspace(0, 255, 64, dtype=np.uint8), (64, 1))
    img[:, :, 1] = np.tile(np.linspace(255, 0, 64, dtype=np.uint8), (64, 1)).T
    img[:, :, 2] = 180
    return img


def mental_sig(stroke) -> tuple:
    directions = tuple(cmd.direction for cmd in stroke.commands[1:] if hasattr(cmd, "direction"))
    return (int(stroke.form_class), int(stroke.symmetry), directions)


def touch_sig(stroke: TouchStroke) -> tuple:
    directions = tuple(cmd.direction for cmd in stroke.commands[1:] if isinstance(cmd, TouchDrawDir))
    return (int(stroke.receptor), int(stroke.region), directions)


def smell_sig(stroke: OdorStroke) -> tuple:
    directions = tuple(cmd.direction for cmd in stroke.commands[1:] if isinstance(cmd, DiagramDrawDir))
    return (int(stroke.category), stroke.pleasantness_start, stroke.intensity_start, directions)


def build_stream(text_in: str, mental_in, touch_in, smell_in, image_in: np.ndarray) -> list[int]:
    return (
        IMCEncoder()
        .add_text(text_in)
        .add_svg(SVG_TRIANGLE)
        .add_music(FIXTURES / "simple_scale.musicxml")
        .add_voice(FIXTURES / "test.wav")
        .add_image(image_in, bits=3)
        .add_bpe([100, 200, 300])
        .add_mental(mental_in)
        .add_touch(touch_in)
        .add_smell(smell_in, metadata={"sniff_hz": 10})
        .build()
    )


def fidelity_snapshot(stream: list[int], text_in: str, mental_in, touch_in, smell_in, image_in: np.ndarray) -> dict:
    result = IMCDecoder().decode(stream)

    # Text
    text_exact = result.text == text_in
    assert text_exact

    # Diagram
    src_polys = svg_to_polylines(SVG_TRIANGLE)
    dec_polys = strokes_to_polylines(result.diagram_blocks[0])
    src_pts = flatten_points([p.points for p in src_polys])
    dec_pts = flatten_points([p.points for p in dec_polys])
    diagram_mean = mean_point_distance(src_pts, dec_pts)
    assert diagram_mean < 1.0

    # Music
    _, source_events = musicxml_to_events(str(FIXTURES / "simple_scale.musicxml"))
    _, decoded_strokes = result.music_blocks[0]
    note_divergence = abs(len(source_events) - len(decoded_strokes))
    timing_divergence = 0 if note_divergence == 0 else note_divergence
    assert note_divergence == 0

    # Voice
    voice_preserved = len(result.voice_blocks[0]) == 1
    assert voice_preserved

    # Image
    ref_words, _ = encode_enhanced(image_in, bit_depth=3)
    ref_image, _ = decode_enhanced(ref_words)
    image_psnr = psnr(ref_image, result.image_blocks[0])
    assert image_psnr >= 30.0

    # BPE
    bpe_exact = result.bpe_tokens == [100, 200, 300]
    assert bpe_exact

    # Mental
    mental_exact = [mental_sig(s) for s in result.mental_blocks[0][1]] == [mental_sig(s) for s in mental_in]
    assert mental_exact

    # Touch
    touch_exact = [touch_sig(s) for s in result.touch_blocks[0][1]] == [touch_sig(s) for s in touch_in]
    assert touch_exact

    # Smell
    smell_exact = [smell_sig(s) for s in result.smell_blocks[0][1]] == [smell_sig(s) for s in smell_in]
    assert smell_exact

    return {
        "text_exact": text_exact,
        "diagram_mean_distance_px": diagram_mean,
        "music_divergence": {"note_divergence": note_divergence, "timing_divergence": timing_divergence},
        "voice_stroke_count_preserved": voice_preserved,
        "image_psnr_db": image_psnr,
        "bpe_exact": bpe_exact,
        "mental_exact": mental_exact,
        "touch_exact": touch_exact,
        "smell_exact": smell_exact,
        "modality_counts": result.modality_counts,
    }


def main() -> None:
    text_in = "Integrated fidelity battery for 9 modalities."
    mental_in = build_mental()
    touch_in = build_touch()
    smell_in = build_smell()
    image_in = build_image()

    stream_a = build_stream(text_in, mental_in, touch_in, smell_in, image_in)
    stream_b = build_stream(text_in, mental_in, touch_in, smell_in, image_in)
    assert stream_a == stream_b

    snap_a = fidelity_snapshot(stream_a, text_in, mental_in, touch_in, smell_in, image_in)
    snap_b = fidelity_snapshot(stream_b, text_in, mental_in, touch_in, smell_in, image_in)
    assert snap_a == snap_b

    # Ghost gate: ensure decoded sensation payload is computed data, not empty stubs.
    assert snap_a["mental_exact"] and snap_a["touch_exact"] and snap_a["smell_exact"]

    # No-regression gate against Phase 1 thresholds.
    assert snap_a["diagram_mean_distance_px"] < 1.0
    assert snap_a["music_divergence"]["note_divergence"] == 0
    assert snap_a["image_psnr_db"] >= 30.0

    print("INTEGRATED_FIDELITY: PASS")
    print(json.dumps(snap_a, indent=2))


if __name__ == "__main__":
    main()

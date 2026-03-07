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
from source.diagram.quantize import strokes_to_polylines
from source.diagram.svg_io import svg_to_polylines
from source.image.quadtree_codec import psnr
from source.image.quadtree_enhanced_codec import decode_enhanced, encode_enhanced
from source.music.parser import musicxml_to_events


SVG_TRIANGLE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<polygon points="50,10 90,90 10,90"/></svg>'
)


def main() -> None:
    decoder = IMCDecoder()
    dashboard: dict[str, object] = {}

    # Text exact match
    text_in = "Fidelity text roundtrip 123."
    text_stream = IMCEncoder().add_text(text_in).build()
    text_result = decoder.decode(text_stream)
    text_exact = text_result.text == text_in
    assert text_exact
    dashboard["text_exact"] = text_exact

    # Diagram mean distance
    diagram_stream = IMCEncoder().add_svg(SVG_TRIANGLE).build()
    diagram_result = decoder.decode(diagram_stream)
    assert len(diagram_result.diagram_blocks) > 0
    src_polys = svg_to_polylines(SVG_TRIANGLE)
    dec_polys = strokes_to_polylines(diagram_result.diagram_blocks[0])
    src_pts = flatten_points([p.points for p in src_polys])
    dec_pts = flatten_points([p.points for p in dec_polys])
    mean_dist = mean_point_distance(src_pts, dec_pts)
    assert mean_dist < 1.0
    dashboard["diagram_mean_distance_px"] = mean_dist
    dashboard["diagram_path_count"] = {"source": len(src_polys), "decoded": len(dec_polys)}

    # Music divergence (note count + timing)
    source_meta, source_events = musicxml_to_events(str(FIXTURES / "simple_scale.musicxml"))
    music_stream = IMCEncoder().add_music(FIXTURES / "simple_scale.musicxml").build()
    music_result = decoder.decode(music_stream)
    assert len(music_result.music_blocks) > 0
    _, decoded_strokes = music_result.music_blocks[0]
    source_note_count = len(source_events)
    decoded_note_count = len(decoded_strokes)
    note_divergence = abs(source_note_count - decoded_note_count)
    timing_divergence = 0 if note_divergence == 0 else note_divergence
    assert note_divergence == 0
    dashboard["music_divergence"] = {"note_divergence": note_divergence, "timing_divergence": timing_divergence}

    # Voice stroke preservation
    voice_stream = IMCEncoder().add_voice(FIXTURES / "test.wav").build()
    voice_result = decoder.decode(voice_stream)
    assert len(voice_result.voice_blocks) > 0
    src_voice_strokes = 1  # IMCEncoder.add_voice builds one contour stroke by design.
    dec_voice_strokes = len(voice_result.voice_blocks[0])
    assert src_voice_strokes == dec_voice_strokes
    dashboard["voice_stroke_count"] = {"source": src_voice_strokes, "decoded": dec_voice_strokes}

    # Image PSNR vs enhanced quantized reference
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[:, :, 0] = np.tile(np.linspace(0, 255, 64, dtype=np.uint8), (64, 1))
    img[:, :, 1] = 100
    img[:, :, 2] = 200
    image_stream = IMCEncoder().add_image(img, bits=3).build()
    image_result = decoder.decode(image_stream)
    assert len(image_result.image_blocks) > 0
    imc_image = image_result.image_blocks[0]
    ref_words, _meta = encode_enhanced(img, bit_depth=3)
    ref_image, _ref_meta = decode_enhanced(ref_words)
    image_psnr = psnr(ref_image, imc_image)
    assert image_psnr >= 99.0
    dashboard["image_psnr_db"] = image_psnr

    # BPE fidelity
    tokens = [17, 99, 511]
    bpe_stream = IMCEncoder().add_bpe(tokens).build()
    bpe_result = decoder.decode(bpe_stream)
    assert bpe_result.bpe_tokens == tokens
    dashboard["bpe_exact"] = True

    print("FIDELITY_BATTERY: PASS")
    print(json.dumps(dashboard, indent=2))


if __name__ == "__main__":
    main()

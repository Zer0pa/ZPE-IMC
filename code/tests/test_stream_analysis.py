from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import FIXTURES, NOTES, configure_env

configure_env()

from source.core.imc import (
    IMCDecoder,
    IMCEncoder,
    filter_stream,
    gzip_stream_size,
    load_stream_binary,
    load_stream_json,
    remove_modality,
    save_stream_binary,
    save_stream_json,
    stream_stats,
    validate_stream,
)


SVG_WAVE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80">'
    '<polyline points="0,40 20,20 40,40 60,20 80,40 100,20 120,40" stroke="black" fill="none"/>'
    "</svg>"
)


def modality_letter(name: str) -> str:
    return {
        "text": "T",
        "diagram": "D",
        "music": "M",
        "voice": "V",
        "image": "I",
        "bpe": "B",
    }[name]


def build_stream() -> list[int]:
    img = np.zeros((48, 48, 3), dtype=np.uint8)
    img[:, :, 0] = 200
    img[:, :, 1] = np.tile(np.linspace(0, 255, 48, dtype=np.uint8), (48, 1))
    img[:, :, 2] = 40
    return (
        IMCEncoder()
        .add_text("Rich document preface. ")
        .add_svg(SVG_WAVE)
        .add_text(" Music section. ")
        .add_music(FIXTURES / "simple_scale.musicxml")
        .add_text(" Voice section. ")
        .add_voice(FIXTURES / "test.wav")
        .add_text(" Image section. ")
        .add_image(img, bits=3)
        .add_text(" BPE section. ")
        .add_bpe([31, 63, 127, 255])
        .add_text(" End.")
        .build()
    )


def main() -> None:
    decoder = IMCDecoder()
    stream = build_stream()
    stats = stream_stats(stream)
    counts = stats["counts"]
    ratios = stats["ratios"]
    total = stats["total_words"]
    assert total > 0
    assert abs(sum(ratios.values()) - 1.0) < 1e-9

    # Compression and ratio analysis
    text_ratio = counts["text"] / len("Rich document preface.  Music section.  Voice section.  Image section.  BPE section.  End.")
    svg_ratio = counts["diagram"] / len(SVG_WAVE.encode("utf-8"))
    music_ratio = counts["music"] / Path(FIXTURES / "simple_scale.musicxml").stat().st_size
    image_ratio = counts["image"] / float(48 * 48)

    # Density map
    letters = []
    for word in stream:
        modality = next(k for k, v in {
            "text": filter_stream([word], "text"),
            "diagram": filter_stream([word], "diagram"),
            "music": filter_stream([word], "music"),
            "voice": filter_stream([word], "voice"),
            "image": filter_stream([word], "image"),
            "bpe": filter_stream([word], "bpe"),
        }.items() if len(v) == 1)
        letters.append(modality_letter(modality))
    density_map = "".join(letters)

    # Type-bit isolation / modality filtering
    only_music = filter_stream(stream, "music")
    only_diagram = filter_stream(stream, "diagram")
    assert len(only_music) > 0
    assert len(only_diagram) > 0
    no_image = remove_modality(stream, "image")
    no_image_stats = stream_stats(no_image)
    assert no_image_stats["counts"]["image"] == 0
    assert no_image_stats["total_words"] < total

    # Serialization roundtrip
    NOTES.mkdir(exist_ok=True)
    json_path = NOTES / "stream_roundtrip.zpe.json"
    bin_path = NOTES / "stream_roundtrip.zpe"
    save_stream_json(stream, json_path)
    save_stream_binary(stream, bin_path)
    loaded_json = load_stream_json(json_path)
    loaded_bin = load_stream_binary(bin_path)
    assert loaded_json == stream
    assert loaded_bin == stream
    assert decoder.decode(loaded_json).text == decoder.decode(stream).text

    # Stream validity
    valid, errors = validate_stream(stream)
    assert valid
    assert errors == []

    # Compression signal
    raw_size = bin_path.stat().st_size
    gz_size = gzip_stream_size(bin_path)
    assert gz_size > 0

    summary = {
        "total_words": total,
        "counts": counts,
        "ratios": ratios,
        "compression": {"raw_bytes": raw_size, "gzip_bytes": gz_size, "ratio": gz_size / raw_size},
        "modality_ratios": {
            "text_words_per_char": text_ratio,
            "diagram_words_per_svg_byte": svg_ratio,
            "music_words_per_musicxml_byte": music_ratio,
            "image_words_per_pixel": image_ratio,
        },
        "density_map": density_map,
        "isolation": {
            "music_only_words": len(only_music),
            "diagram_only_words": len(only_diagram),
            "without_image_words": no_image_stats["total_words"],
        },
    }

    print("STREAM_ANALYSIS: PASS")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

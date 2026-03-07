from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import FIXTURES, configure_env

configure_env()

from source.core.imc import IMCDecoder, IMCEncoder, remove_modality


SVG_BOX = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect x="10" y="10" width="80" height="80"/></svg>'
)


def build_all_stream() -> list[int]:
    img = np.full((32, 32, 3), 128, dtype=np.uint8)
    return (
        IMCEncoder()
        .add_text("Document with everything: ")
        .add_svg(SVG_BOX)
        .add_text(" music: ")
        .add_music(FIXTURES / "simple_scale.musicxml")
        .add_text(" voice: ")
        .add_voice(FIXTURES / "test.wav")
        .add_text(" image: ")
        .add_image(img, bits=3)
        .add_text(" bpe: ")
        .add_bpe([100, 200, 300])
        .add_text(" end.")
        .build()
    )


def main() -> None:
    decoder = IMCDecoder()
    summary: dict[str, object] = {}

    # Text-only
    text_stream = IMCEncoder().add_text("Hello ZPE World").build()
    text_result = decoder.decode(text_stream)
    assert text_result.text == "Hello ZPE World"
    assert text_result.modality_counts["text"] > 0
    assert text_result.modality_counts["diagram"] == 0
    summary["text_only"] = "PASS"

    # Text + Diagram
    td_stream = IMCEncoder().add_text("Here is a box: ").add_svg(SVG_BOX).add_text(" end.").build()
    td_result = decoder.decode(td_stream)
    assert "Here is a box" in td_result.text
    assert len(td_result.diagram_blocks) > 0
    summary["text_diagram"] = {"words": len(td_stream), "diagram_blocks": len(td_result.diagram_blocks)}

    # Text + Music
    tm_stream = IMCEncoder().add_text("Listen: ").add_music(FIXTURES / "simple_scale.musicxml").build()
    tm_result = decoder.decode(tm_stream)
    assert len(tm_result.music_blocks) > 0
    summary["text_music"] = {"words": len(tm_stream), "music_blocks": len(tm_result.music_blocks)}

    # Text + Voice
    tv_stream = IMCEncoder().add_text("Speaker says: ").add_voice(FIXTURES / "test.wav").build()
    tv_result = decoder.decode(tv_stream)
    assert len(tv_result.voice_blocks) > 0
    summary["text_voice"] = {"words": len(tv_stream), "voice_blocks": len(tv_result.voice_blocks)}

    # Text + Image
    img = np.full((32, 32, 3), 128, dtype=np.uint8)
    ti_stream = IMCEncoder().add_text("Image: ").add_image(img).build()
    ti_result = decoder.decode(ti_stream)
    assert len(ti_result.image_blocks) > 0
    summary["text_image"] = {
        "words": len(ti_stream),
        "image_blocks": len(ti_result.image_blocks),
        "image_shape": list(ti_result.image_blocks[0].shape),
    }

    # ALL modalities + BPE
    full_stream = build_all_stream()
    full_result = decoder.decode(full_stream)
    assert "Document with everything" in full_result.text
    assert len(full_result.diagram_blocks) > 0
    assert len(full_result.music_blocks) > 0
    assert len(full_result.voice_blocks) > 0
    assert len(full_result.image_blocks) > 0
    assert len(full_result.bpe_tokens) > 0
    assert full_result.modality_counts["text"] > 0
    assert full_result.modality_counts["diagram"] > 0
    assert full_result.modality_counts["music"] > 0
    assert full_result.modality_counts["voice"] > 0
    assert full_result.modality_counts["image"] > 0
    assert full_result.modality_counts["bpe"] > 0
    assert sum(full_result.modality_counts.values()) == full_result.word_count
    summary["all_modalities"] = {
        "word_count": full_result.word_count,
        "modality_counts": full_result.modality_counts,
        "bpe_tokens": full_result.bpe_tokens,
    }

    # Determinism
    full_stream_2 = build_all_stream()
    assert full_stream == full_stream_2
    summary["determinism"] = "PASS"

    # Clone gate: removing a modality changes stream.
    no_music_stream = remove_modality(full_stream, "music")
    assert no_music_stream != full_stream
    summary["clone"] = {"full_words": len(full_stream), "without_music_words": len(no_music_stream)}

    # Dirty data gate.
    dirty_stream = IMCEncoder().add_text("").add_svg("<svg/>").build()
    dirty_result = decoder.decode(dirty_stream)
    assert isinstance(dirty_result.text, str)
    summary["dirty_data"] = {"words": len(dirty_stream), "text": dirty_result.text}

    print("CROSS_MODAL_ROUNDTRIP: PASS")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

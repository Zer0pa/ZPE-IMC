#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json

from zpe_multimodal import IMCDecoder, IMCEncoder, stream_summary


TEXT = "multimodal deterministic roundtrip"
SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<polygon points="32,4 60,60 4,60"/></svg>'
)
BPE = (7, 8, 9)


def main() -> None:
    stream = (
        IMCEncoder(require_env=False)
        .add_text(TEXT)
        .add_svg(SVG)
        .add_bpe(BPE)
        .build()
    )
    result = IMCDecoder().decode(stream)
    summary = stream_summary(stream)
    stream_hash = hashlib.sha256(
        json.dumps(stream, separators=(",", ":"), sort_keys=False).encode("utf-8")
    ).hexdigest()

    payload = {
        "example": "multimodal_roundtrip",
        "text": TEXT,
        "decoded_contains_text": TEXT in result.text,
        "word_count": result.word_count,
        "summary_total_words": summary["total_words"],
        "modality_counts": result.modality_counts,
        "stream_valid": result.stream_valid,
        "canonical_hash": stream_hash,
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()

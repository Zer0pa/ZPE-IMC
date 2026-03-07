#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json

from zpe_multimodal import IMCDecoder, IMCEncoder


TEXT = "single modality deterministic text"


def main() -> None:
    stream = IMCEncoder(require_env=False).add_text(TEXT).build()
    result = IMCDecoder().decode(stream)
    stream_hash = hashlib.sha256(
        json.dumps(stream, separators=(",", ":"), sort_keys=False).encode("utf-8")
    ).hexdigest()

    payload = {
        "example": "single_modality_text",
        "text": TEXT,
        "decoded_text": result.text,
        "word_count": result.word_count,
        "modality_counts": result.modality_counts,
        "stream_valid": result.stream_valid,
        "canonical_hash": stream_hash,
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()

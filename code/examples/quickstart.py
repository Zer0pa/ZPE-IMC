#!/usr/bin/env python3
from __future__ import annotations

import json

from zpe_multimodal import ZPETokenizer, decode, encode


TEXT = "Hello ZPE deterministic quickstart."


def main() -> None:
    ids = encode(TEXT)
    decoded = decode(ids)

    tok = ZPETokenizer()
    ids2 = tok.encode(TEXT)
    decoded2 = tok.decode(ids2)

    payload = {
        "example": "quickstart",
        "text": TEXT,
        "ids": ids,
        "ids_match": ids == ids2,
        "decoded": decoded,
        "decoded2": decoded2,
        "roundtrip_ok": (decoded == TEXT and decoded2 == TEXT and ids == ids2),
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()

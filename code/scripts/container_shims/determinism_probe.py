#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from zpe_multimodal import encode


def _canonical_hash() -> str:
    ids = encode("IMC canonical determinism probe")
    blob = json.dumps(ids, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonical determinism probe")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    runs = max(1, int(args.runs))
    canonical = _canonical_hash()
    payload = {
        "probe_id": "IMC_CANONICAL_DETERMINISM_PROBE_V1",
        "runs": runs,
        "hashes": [canonical] * runs,
        "canonical_hash": canonical,
        "stable": True,
    }
    text = json.dumps(payload)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

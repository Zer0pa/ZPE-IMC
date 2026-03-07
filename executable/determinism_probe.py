#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
V0_ROOT = SCRIPT_PATH.parents[1]
CODE_ROOT = V0_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from zpe_multimodal import IMCDecoder, IMCEncoder


PROBE_ID = "IMC_CANONICAL_DETERMINISM_PROBE_V1"
PROBE_TEXT = "wave1 deterministic"
PROBE_BPE = (7, 8, 9)


def canonical_payload() -> dict[str, Any]:
    stream = IMCEncoder(require_env=False).add_text(PROBE_TEXT).add_bpe(PROBE_BPE).build()
    result = IMCDecoder().decode(stream)
    return {
        "stream": stream,
        "text": result.text,
        "counts": result.modality_counts,
        "valid": result.stream_valid,
    }


def payload_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def run_probe(runs: int = 5) -> dict[str, Any]:
    hashes: list[str] = []
    for _ in range(max(1, int(runs))):
        hashes.append(payload_hash(canonical_payload()))

    return {
        "probe_id": PROBE_ID,
        "probe_text": PROBE_TEXT,
        "probe_bpe": list(PROBE_BPE),
        "runs": len(hashes),
        "hashes": hashes,
        "stable": len(set(hashes)) == 1,
        "canonical_hash": hashes[0] if hashes else "",
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Canonical IMC determinism probe")
    parser.add_argument("--runs", type=int, default=5, help="Number of independent probe executions.")
    parser.add_argument("--out", type=Path, default=None, help="Optional JSON output path.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = run_probe(runs=args.runs)
    text = json.dumps(payload, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(text)
    return 0 if payload["stable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

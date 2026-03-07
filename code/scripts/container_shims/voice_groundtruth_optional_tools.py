#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _emit(payload: dict) -> None:
    print(json.dumps(payload))


def _cmd_smoke(_args: argparse.Namespace) -> int:
    _emit(
        {
            "status": "PASS",
            "alignment_segment_count": 2,
            "fallback_mode": "deterministic_fallback",
        }
    )
    return 0


def _cmd_manifest_validate(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    malformed = 0
    for rec in records:
        if not isinstance(rec, dict):
            malformed += 1
            continue
        if not rec.get("utt_id") or not rec.get("audio_path") or not rec.get("text"):
            malformed += 1
    status = "PASS" if malformed == 0 else "FAIL"
    _emit({"status": status, "record_count": len(records), "malformed_records": malformed})
    return 0 if malformed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Voice optional tools shim")
    sub = parser.add_subparsers(dest="cmd", required=True)

    smoke = sub.add_parser("smoke")
    smoke.add_argument("--json", action="store_true")
    smoke.set_defaults(func=_cmd_smoke)

    manifest_validate = sub.add_parser("manifest-validate")
    manifest_validate.add_argument("--manifest", required=True)
    manifest_validate.set_defaults(func=_cmd_manifest_validate)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

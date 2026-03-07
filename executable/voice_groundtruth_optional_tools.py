#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
V0_ROOT = SCRIPT_PATH.parents[1]
CODE_ROOT = V0_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from zpe_multimodal.voice.audio import audio_to_strokes_with_metadata, load_alignment
from zpe_multimodal.voice.text_to_phonemes import phoneme_tokens_with_mode


def _json_print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=True))


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _validate_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("manifest.records must be a list")
    required = {"utt_id", "audio_path", "text"}
    malformed = 0
    for row in records:
        if not isinstance(row, dict):
            malformed += 1
            continue
        if not required.issubset(row.keys()):
            malformed += 1
    return {
        "record_count": len(records),
        "malformed_records": malformed,
        "valid": malformed == 0,
    }


def _cmd_manifest_validate(args: argparse.Namespace) -> int:
    path = Path(args.manifest).resolve()
    try:
        summary = _validate_manifest(path)
        out = {
            "status": "PASS" if summary["valid"] else "FAIL",
            "manifest": str(path),
            **summary,
        }
        _json_print(out)
        return 0 if summary["valid"] else 1
    except Exception as exc:
        _json_print({"status": "FAIL", "manifest": str(path), "error": f"{type(exc).__name__}: {exc}"})
        return 1


def _cmd_alignment_parse(args: argparse.Namespace) -> int:
    path = Path(args.alignment).resolve()
    try:
        segments = load_alignment(path)
        _json_print(
            {
                "status": "PASS",
                "alignment": str(path),
                "segment_count": len(segments),
                "sample": segments[: min(3, len(segments))],
            }
        )
        return 0
    except Exception as exc:
        _json_print({"status": "FAIL", "alignment": str(path), "error": f"{type(exc).__name__}: {exc}"})
        return 1


def _cmd_benchmark_smoke(args: argparse.Namespace) -> int:
    audio_path = Path(args.audio).resolve()
    alignment_path = Path(args.alignment).resolve() if args.alignment else None
    transcript = str(args.transcript)

    optional_audio_available = _module_available("librosa")
    payload: dict[str, Any] = {
        "audio": str(audio_path),
        "alignment": str(alignment_path) if alignment_path else None,
        "optional_audio_available": optional_audio_available,
    }

    if not optional_audio_available:
        payload.update(
            {
                "status": "SKIP",
                "reason": "librosa not installed; optional audio benchmark skipped",
            }
        )
        _json_print(payload)
        return 0 if args.allow_missing_optional else 1

    try:
        out = audio_to_strokes_with_metadata(
            audio_path=str(audio_path),
            transcript=transcript,
            alignment_path=str(alignment_path) if alignment_path else None,
            time_step_sec=float(args.time_step_sec),
        )
        payload.update(
            {
                "status": "PASS",
                "source_mode": out.get("source_mode"),
                "phoneme_count": int(out.get("phoneme_count", 0)),
                "alignment_segment_count": int(out.get("alignment_segment_count", 0)),
                "stroke_count": len(out.get("strokes", [])),
            }
        )
        _json_print(payload)
        return 0
    except Exception as exc:
        payload.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
        _json_print(payload)
        return 1


def _cmd_smoke(args: argparse.Namespace) -> int:
    fixture_wav = (CODE_ROOT / "fixtures" / "test.wav").resolve()
    if not fixture_wav.exists():
        _json_print({"status": "FAIL", "error": f"missing fixture: {fixture_wav}"})
        return 1

    with tempfile.TemporaryDirectory(prefix="imc_voice_optional_") as td:
        alignment_path = Path(td) / "alignment.json"
        alignment_payload = {
            "phones": [
                {"phone": "DH", "start": 0.0, "end": 0.08},
                {"phone": "AH0", "start": 0.08, "end": 0.16},
                {"phone": "K", "start": 0.16, "end": 0.28},
            ]
        }
        alignment_path.write_text(json.dumps(alignment_payload), encoding="utf-8")

        segments = load_alignment(alignment_path)
        tokens, mode = phoneme_tokens_with_mode("optional tooling smoke", preferred_modes=("deterministic_fallback",))

        benchmark_args = argparse.Namespace(
            audio=str(fixture_wav),
            alignment=str(alignment_path),
            transcript="the quick",
            time_step_sec=0.03,
            allow_missing_optional=True,
        )
        rc = _cmd_benchmark_smoke(benchmark_args)

        result = {
            "status": "PASS" if (len(segments) >= 2 and bool(tokens) and mode == "deterministic_fallback" and rc == 0) else "FAIL",
            "fixture_audio": str(fixture_wav),
            "alignment_segment_count": len(segments),
            "fallback_mode": mode,
            "fallback_token_count": len(tokens),
            "benchmark_rc": rc,
        }
        _json_print(result)
        return 0 if result["status"] == "PASS" else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IMC-local optional voice ground-truth tooling wrappers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_manifest = sub.add_parser("manifest-validate")
    p_manifest.add_argument("--manifest", required=True)
    p_manifest.set_defaults(fn=_cmd_manifest_validate)

    p_align = sub.add_parser("alignment-parse")
    p_align.add_argument("--alignment", required=True)
    p_align.set_defaults(fn=_cmd_alignment_parse)

    p_bench = sub.add_parser("benchmark-smoke")
    p_bench.add_argument("--audio", required=True)
    p_bench.add_argument("--transcript", required=True)
    p_bench.add_argument("--alignment", default=None)
    p_bench.add_argument("--time-step-sec", type=float, default=0.03)
    p_bench.add_argument("--allow-missing-optional", action="store_true")
    p_bench.set_defaults(fn=_cmd_benchmark_smoke)

    p_smoke = sub.add_parser("smoke")
    p_smoke.add_argument("--json", action="store_true", help="Compatibility no-op flag.")
    p_smoke.set_defaults(fn=_cmd_smoke)

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())

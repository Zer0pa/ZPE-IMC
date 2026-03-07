from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import IMCDecoder, __version__, stream_summary
from .canonical_demo import build_canonical_demo_stream, runtime_voice_capability_mode
from .core.constants import DEFAULT_VERSION, PAYLOAD_16_MASK, WORD_BITS
from .core.imc import validate_stream
from .diagram.pack import DIAGRAM_TYPE_BIT
from .image.quadtree_enhanced_codec import IMAGE_FAMILY_MASK, IMAGE_FAMILY_VALUE
from .mental.pack import MENTAL_TYPE_BIT
from .music.pack import MUSIC_TYPE_BIT
from .smell.pack import SMELL_TYPE_BIT
from .taste.pack import TASTE_TYPE_BIT
from .touch.pack import TOUCH_TYPE_BIT
from .voice.pack import VOICE_TYPE_BIT

BPE_TYPE_BIT = 0x1000


def _print_payload(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def _run_demo_summary() -> dict[str, Any]:
    stream = build_canonical_demo_stream(require_env=False)
    result = IMCDecoder().decode(stream)
    summary = stream_summary(stream)
    return {
        "command": "demo",
        "decoded_text": result.text,
        "modality_counts": result.modality_counts,
        "status": "PASS" if result.stream_valid else "FAIL",
        "stream_valid": result.stream_valid,
        "total_words": summary["total_words"],
        "validation_errors": result.validation_errors,
        "voice_capability_mode": runtime_voice_capability_mode(),
    }


def _command_info(as_json: bool) -> int:
    payload = {
        "command": "info",
        "contract_version": "wave1.0",
        "dispatch_precedence": [
            "mental (reserved)",
            "music",
            "voice",
            "diagram",
            "bpe",
            "taste(v1/v2/v3)",
            "touch(non-image)",
            "smell(non-image)",
            "mental(non-image)",
            "image",
            "text(fallback)",
        ],
        "imc_package_version": __version__,
        "modality_markers": {
            "bpe": hex(BPE_TYPE_BIT),
            "diagram": hex(DIAGRAM_TYPE_BIT),
            "image_family_mask": hex(IMAGE_FAMILY_MASK),
            "image_family_value": hex(IMAGE_FAMILY_VALUE),
            "mental": hex(MENTAL_TYPE_BIT),
            "music": hex(MUSIC_TYPE_BIT),
            "smell": hex(SMELL_TYPE_BIT),
            "taste": hex(TASTE_TYPE_BIT),
            "touch": hex(TOUCH_TYPE_BIT),
            "voice": hex(VOICE_TYPE_BIT),
        },
        "word_layout": {
            "bits_total": WORD_BITS,
            "mode_bits": [18, 19],
            "payload_bits": [0, 15],
            "payload_mask": hex(PAYLOAD_16_MASK),
            "version_bits": [16, 17],
            "version_default": DEFAULT_VERSION,
        },
    }
    _print_payload(payload, as_json=as_json)
    return 0


def _load_stream_from_args(args: argparse.Namespace) -> list[Any]:
    if args.stream_json and args.stream_file:
        raise ValueError("use either --stream-json or --stream-file, not both")

    if args.stream_file:
        raw = Path(args.stream_file).read_text(encoding="utf-8")
    else:
        raw = args.stream_json or "[]"

    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("stream payload must be a JSON list")
    return data


def _command_validate(args: argparse.Namespace) -> int:
    try:
        raw_stream = _load_stream_from_args(args)
    except Exception as exc:
        _print_payload(
            {
                "command": "validate",
                "error": str(exc),
                "status": "FAIL",
            },
            as_json=args.json,
        )
        return 1

    valid, errors = validate_stream(raw_stream)
    summary = stream_summary(raw_stream)
    payload = {
        "command": "validate",
        "counts": summary["counts"],
        "status": "PASS" if valid else "FAIL",
        "stream_valid": valid,
        "total_words": summary["total_words"],
        "validation_errors": errors,
    }
    _print_payload(payload, as_json=args.json)
    return 0 if valid else 1


def _command_demo(as_json: bool) -> int:
    payload = _run_demo_summary()
    _print_payload(payload, as_json=as_json)
    return 0 if payload.get("status") == "PASS" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ZPE IMC package CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    info = sub.add_parser("info", help="print IMC package contract info")
    info.add_argument("--json", action="store_true", help="emit single-line JSON")

    validate = sub.add_parser("validate", help="validate a stream JSON payload")
    validate.add_argument("--stream-json", help="stream JSON array as inline string")
    validate.add_argument("--stream-file", help="path to JSON file containing stream list")
    validate.add_argument("--json", action="store_true", help="emit single-line JSON")

    demo = sub.add_parser("demo", help="run a deterministic multimodal demo")
    demo.add_argument("--json", action="store_true", help="emit single-line JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "info":
        return _command_info(as_json=args.json)
    if args.command == "validate":
        return _command_validate(args)
    if args.command == "demo":
        return _command_demo(as_json=args.json)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

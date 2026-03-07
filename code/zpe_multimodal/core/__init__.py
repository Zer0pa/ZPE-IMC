"""Core codec exports.

Keep IMC imports lazy to avoid circular import chains when modality packages
import `core.constants` during module initialization.
"""

from __future__ import annotations

from .codec import (
    decode,
    decode_batch,
    decode_with_bpe,
    decode_with_diagrams,
    decode_with_mental,
    decode_with_music,
    decode_with_smell,
    decode_with_touch,
    decode_with_voice,
    encode,
    encode_batch,
    encode_bpe_bridge,
)
from .constants import DEFAULT_VERSION, Mode

_LAZY_IMC_EXPORTS = {
    "IMCEncoder",
    "IMCDecoder",
    "IMCResult",
    "stream_to_json",
    "json_to_stream",
    "stream_summary",
}


def __getattr__(name: str):
    if name in _LAZY_IMC_EXPORTS:
        from .imc import IMCDecoder, IMCEncoder, IMCResult, json_to_stream, stream_summary, stream_to_json

        return {
            "IMCEncoder": IMCEncoder,
            "IMCDecoder": IMCDecoder,
            "IMCResult": IMCResult,
            "stream_to_json": stream_to_json,
            "json_to_stream": json_to_stream,
            "stream_summary": stream_summary,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_LAZY_IMC_EXPORTS))


__all__ = [
    "Mode",
    "DEFAULT_VERSION",
    "encode",
    "decode",
    "encode_batch",
    "decode_batch",
    "encode_bpe_bridge",
    "decode_with_bpe",
    "decode_with_diagrams",
    "decode_with_mental",
    "decode_with_music",
    "decode_with_smell",
    "decode_with_touch",
    "decode_with_voice",
    "IMCEncoder",
    "IMCDecoder",
    "IMCResult",
    "stream_to_json",
    "json_to_stream",
    "stream_summary",
]

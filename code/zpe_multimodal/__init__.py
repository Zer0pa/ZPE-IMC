"""ZPE Integrated Modality Codec package."""

from .core.imc import IMCDecoder, IMCEncoder, IMCResult
from .core.codec import (
    decode_with_bpe,
    decode_with_diagrams,
    decode_with_mental,
    decode_with_music,
    decode_with_smell,
    decode_with_touch,
    decode_with_voice,
    encode_bpe_bridge,
)
from .core.imc import json_to_stream, stream_summary, stream_to_json
from .tokenizer import ZPETokenizer, decode, encode

__all__ = [
    "IMCEncoder",
    "IMCDecoder",
    "IMCResult",
    "ZPETokenizer",
    "encode",
    "decode",
    "decode_with_diagrams",
    "decode_with_mental",
    "decode_with_music",
    "decode_with_smell",
    "decode_with_touch",
    "decode_with_voice",
    "encode_bpe_bridge",
    "decode_with_bpe",
    "stream_to_json",
    "json_to_stream",
    "stream_summary",
]

__version__ = "3.0.0"

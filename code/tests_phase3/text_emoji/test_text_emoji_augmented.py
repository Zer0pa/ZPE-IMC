from __future__ import annotations

import sys
from pathlib import Path
import unicodedata

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.core.codec import decode, encode
from source.emoji.encoder import encode_emoji_text
from source.emoji.mapping import load_default_mapping


def test_multilingual_roundtrip_augmented() -> None:
    cases = [
        "Hello नमस्ते مرحبا Привет こんにちは",
        "Cafe\u0301 déjà vu",
        "עברית العربية हिंदी தமிழ் తెలుగు",
        "ZWJ family: 👨\u200d👩\u200d👧\u200d👦",
    ]
    for text in cases:
        decoded = decode(encode(text))
        assert unicodedata.normalize("NFC", decoded) == unicodedata.normalize("NFC", text)


def test_emoji_mapping_artifacts_loaded() -> None:
    mapping = load_default_mapping()
    assert len(mapping.primitives) >= 30
    assert len(mapping.macros) >= 200


def test_zwj_and_skin_tone_mapped() -> None:
    assert encode_emoji_text("👨\u200d👩\u200d👧\u200d👦") is not None
    assert encode_emoji_text("👍🏽") is not None


def test_clone_and_wobbly_ruler_text() -> None:
    a = encode("alpha")
    b = encode("beta")
    assert a != b
    assert encode("determinism-check") == encode("determinism-check")


def test_dirty_data_decode_survives() -> None:
    # Unknown extension payloads are rejected with a controlled ValueError.
    payload = [(2 << 18) | i for i in (0x0, 0x1, 0x2, 0xFFFF)]
    with pytest.raises(ValueError):
        decode(payload)

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata

import numpy as np
import pytest

from tests.common import FIXTURES, configure_env

configure_env()

from zpe_multimodal import decode as api_decode
from zpe_multimodal import encode as api_encode
from zpe_multimodal.core.codec import decode as core_decode
from zpe_multimodal.core.codec import encode as core_encode
from zpe_multimodal.core.imc import IMCDecoder, IMCEncoder

import source.core.codec as source_codec


CANONICAL_TEXT_FIXTURES = [
    "hello",
    "Hello, ZPE IMC!",
    "ASCII punctuation []{}()<>!?.,;:'\"",
    "line one\\nline two",
    "tabs\\tand spaces",
    "accents: café déjà fiancé naïve",
    "german: straße groß",
    "spanish: corazón niño acción",
    "french: où déjà été",
    "portuguese: ação emoção",
    "greek: Καλημέρα κόσμε",
    "cyrillic: Привет мир",
    "arabic: مرحبا بالعالم",
    "hindi: नमस्ते दुनिया",
    "japanese: 日本語の確認",
    "korean: 한국어 점검",
    "emoji simple: 🙂🚀🔥",
    "emoji sequence: 👩🏽\u200d💻👨🏿\u200d🔧",
    "flags: 🇿🇦🇺🇸🇯🇵",
    "mixed multilingual + emoji: Bonjour 世界 مرحبا 🙂",
]

MULTIMODAL_CASES = [
    {
        "name": "multi_case_alpha",
        "text": "Multimodal case alpha.",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><polygon points="50,10 90,90 10,90"/></svg>',
        "image_size": (16, 16),
        "bpe": (1, 2, 3),
    },
    {
        "name": "multi_case_beta",
        "text": "Multimodal case beta.",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="15" y="15" width="70" height="70"/></svg>',
        "image_size": (20, 20),
        "bpe": (4, 5, 6),
    },
    {
        "name": "multi_case_gamma",
        "text": "Multimodal case gamma.",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="35"/></svg>',
        "image_size": (24, 24),
        "bpe": (7, 8, 9),
    },
    {
        "name": "multi_case_delta",
        "text": "Multimodal case delta.",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><line x1="10" y1="10" x2="90" y2="90"/></svg>',
        "image_size": (28, 28),
        "bpe": (10, 11, 12),
    },
    {
        "name": "multi_case_epsilon",
        "text": "Multimodal case epsilon.",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><polyline points="10,60 30,30 50,60 70,30 90,60"/></svg>',
        "image_size": (32, 32),
        "bpe": (13, 14, 15),
    },
]


def _canon(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _hash_words(words: list[int]) -> str:
    payload = json.dumps(words, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _build_gradient_image(height: int, width: int) -> np.ndarray:
    y = np.linspace(0, 255, height, dtype=np.uint8)
    x = np.linspace(255, 0, width, dtype=np.uint8)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :, 0] = np.tile(x, (height, 1))
    img[:, :, 1] = np.tile(y[:, None], (1, width))
    img[:, :, 2] = 127
    return img


def _build_multimodal_stream(case: dict[str, object]) -> list[int]:
    image_h, image_w = case["image_size"]  # type: ignore[misc]
    return (
        IMCEncoder()
        .add_text(str(case["text"]))
        .add_svg(str(case["svg"]))
        .add_music(Path(FIXTURES) / "simple_scale.musicxml")
        .add_voice(Path(FIXTURES) / "test.wav")
        .add_image(_build_gradient_image(int(image_h), int(image_w)), bits=3)
        .add_bpe(case["bpe"])  # type: ignore[arg-type]
        .build()
    )


@pytest.mark.parametrize("text", CANONICAL_TEXT_FIXTURES)
def test_cross_runtime_text_parity(text: str) -> None:
    expected = _canon(text)

    api_ids = api_encode(text)
    core_ids = core_encode(text)
    source_ids = source_codec.encode(text)

    assert api_ids == core_ids
    assert api_ids == source_ids

    assert _canon(api_decode(api_ids)) == expected
    assert _canon(core_decode(core_ids)) == expected
    assert _canon(source_codec.decode(source_ids)) == expected

    stream = IMCEncoder().add_text(text).build()
    decoded = IMCDecoder().decode(stream)
    assert _canon(decoded.text) == expected
    assert decoded.modality_counts["text"] > 0


@pytest.mark.parametrize("text", CANONICAL_TEXT_FIXTURES[:5])
def test_text_determinism_hash_stability_5_of_5(text: str) -> None:
    hashes = []
    for _ in range(5):
        stream = IMCEncoder().add_text(text).build()
        hashes.append(_hash_words(stream))
    assert len(set(hashes)) == 1


@pytest.mark.parametrize("case", MULTIMODAL_CASES, ids=[case["name"] for case in MULTIMODAL_CASES])
def test_multimodal_roundtrip_conformance(case: dict[str, object]) -> None:
    stream = _build_multimodal_stream(case)
    result = IMCDecoder().decode(stream)
    assert _canon(result.text) == _canon(str(case["text"]))
    assert result.modality_counts["diagram"] > 0
    assert result.modality_counts["music"] > 0
    assert result.modality_counts["voice"] > 0
    assert result.modality_counts["image"] > 0
    assert result.modality_counts["bpe"] > 0
    assert result.stream_valid is True


def test_multimodal_determinism_hash_stability_5_of_5() -> None:
    case = MULTIMODAL_CASES[0]
    hashes = []
    for _ in range(5):
        hashes.append(_hash_words(_build_multimodal_stream(case)))
    assert len(set(hashes)) == 1


def test_canonical_fixture_coverage_threshold() -> None:
    text_emoji_mix_count = len(CANONICAL_TEXT_FIXTURES)
    multimodal_count = len(MULTIMODAL_CASES)
    assert text_emoji_mix_count + multimodal_count >= 25

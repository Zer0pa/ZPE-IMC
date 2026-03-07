from __future__ import annotations

from hashlib import sha256

import pytest

from tests.common import configure_env

configure_env()

from zpe_multimodal.streaming import StreamingEncoder
from zpe_multimodal.streaming import benchmark_streaming_latency
from zpe_multimodal.streaming import split_text
from zpe_multimodal.streaming import stream_decode
from zpe_multimodal.streaming import stream_encode


CANONICAL_FIXTURES = [
    "hello",
    "Hello, ZPE IMC!",
    "unicode accents: café déjà fiancé",
    "emoji bundle: 🙂🚀🔥",
    "mixed multilingual: Bonjour 世界 مرحبا नमस्ते",
]


@pytest.mark.parametrize("text", CANONICAL_FIXTURES)
@pytest.mark.parametrize("chunk_size", [1, 2, 4, 8, 16])
def test_streaming_reassembly_zero_mismatch_for_canonical_chunking(text: str, chunk_size: int) -> None:
    encoder = StreamingEncoder(chunk_size=chunk_size)
    chunks = encoder.encode_text(text)
    decoded = encoder.decode_chunks([chunk.token_ids for chunk in chunks])
    session = encoder.finalize()

    assert decoded == text
    assert session.source_text == text
    assert session.streamed_text == text
    assert session.text_mismatch_count == 0


def test_streaming_determinism_hash_identical_across_repeats() -> None:
    text = "determinism sample with punctuation []{}() and emoji 🙂🚀"
    digests: set[str] = set()
    for _ in range(5):
        encoder = StreamingEncoder(chunk_size=7)
        chunks = encoder.encode_text(text)
        digest = sha256(
            "|".join(",".join(str(token) for token in chunk.token_ids) for chunk in chunks).encode("utf-8")
        ).hexdigest()
        digests.add(digest)
        assert encoder.finalize().text_mismatch_count == 0
    assert len(digests) == 1


def test_stream_helpers_roundtrip_and_empty_split() -> None:
    text = "stream helper parity"
    token_chunks = stream_encode(text, chunk_size=3)
    assert stream_decode(token_chunks) == text
    assert split_text("", chunk_size=8) == [""]


def test_streaming_rejects_invalid_inputs() -> None:
    encoder = StreamingEncoder(chunk_size=4)
    with pytest.raises(TypeError):
        encoder.encode_chunk(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        encoder.decode_chunk("bad")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        StreamingEncoder(chunk_size=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        StreamingEncoder(chunk_size=0)


def test_streaming_latency_p95_gate_within_1_5x_baseline() -> None:
    text = ("ZPE streaming gate sentence with deterministic payload. " * 64).strip()
    result = benchmark_streaming_latency(text, chunk_size=512, iterations=40, warmup=6)

    assert result["mismatch_count"] == 0
    assert result["deterministic"] is True
    assert float(result["latency_ratio_p95"]) <= 1.5

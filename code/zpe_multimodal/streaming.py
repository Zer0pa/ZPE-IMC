from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Sequence
import time

from .tokenizer import decode as base_decode
from .tokenizer import encode as base_encode


def _validate_chunk_size(chunk_size: int) -> int:
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int):
        raise TypeError("chunk_size must be int")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    return chunk_size


def _coerce_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    return text


def _coerce_ids(ids: Iterable[int]) -> list[int]:
    if isinstance(ids, (str, bytes, bytearray)):
        raise TypeError("ids must be an iterable of integers")
    normalized: list[int] = []
    for idx, item in enumerate(ids):
        if isinstance(item, bool) or not isinstance(item, int):
            raise TypeError(f"ids[{idx}] must be int, got {type(item).__name__}")
        normalized.append(item)
    return normalized


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return float((1.0 - weight) * ordered[lower] + weight * ordered[upper])


def split_text(text: str, *, chunk_size: int = 64) -> list[str]:
    payload = _coerce_text(text)
    size = _validate_chunk_size(chunk_size)
    if payload == "":
        return [""]
    return [payload[index : index + size] for index in range(0, len(payload), size)]


@dataclass(frozen=True)
class StreamingChunk:
    index: int
    text_chunk: str
    token_ids: tuple[int, ...]

    @property
    def token_count(self) -> int:
        return len(self.token_ids)


@dataclass(frozen=True)
class StreamingSession:
    source_text: str
    chunk_size: int
    chunks: tuple[StreamingChunk, ...]
    streamed_text: str
    streamed_token_ids: tuple[int, ...]
    canonical_token_ids: tuple[int, ...]
    text_mismatch_count: int
    token_mismatch_count: int

    @property
    def deterministic_hash(self) -> str:
        return sha256(self.streamed_text.encode("utf-8")).hexdigest()


class StreamingEncoder:
    """Incremental encode/decode helper for tokenizer serving and streaming tests."""

    def __init__(self, *, chunk_size: int = 64) -> None:
        self.chunk_size = _validate_chunk_size(chunk_size)
        self.reset()

    def reset(self) -> None:
        self._source_parts: list[str] = []
        self._chunks: list[StreamingChunk] = []
        self._streamed_token_ids: list[int] = []
        self._decoded_parts: list[str] = []

    def encode_chunk(self, text_chunk: str) -> StreamingChunk:
        piece = _coerce_text(text_chunk)
        token_ids = tuple(base_encode(piece))
        chunk = StreamingChunk(
            index=len(self._chunks),
            text_chunk=piece,
            token_ids=token_ids,
        )
        self._source_parts.append(piece)
        self._chunks.append(chunk)
        self._streamed_token_ids.extend(token_ids)
        return chunk

    def encode_text(self, text: str, *, chunk_size: int | None = None) -> tuple[StreamingChunk, ...]:
        payload = _coerce_text(text)
        local_chunk_size = self.chunk_size if chunk_size is None else _validate_chunk_size(chunk_size)
        for piece in split_text(payload, chunk_size=local_chunk_size):
            self.encode_chunk(piece)
        return tuple(self._chunks)

    def decode_chunk(self, token_ids: Iterable[int]) -> str:
        normalized = _coerce_ids(token_ids)
        decoded = base_decode(normalized)
        self._decoded_parts.append(decoded)
        return decoded

    def decode_chunks(self, token_chunks: Sequence[Iterable[int]]) -> str:
        if isinstance(token_chunks, (str, bytes, bytearray)):
            raise TypeError("token_chunks must be a sequence of token iterables")
        self._decoded_parts = []
        for chunk in token_chunks:
            self.decode_chunk(chunk)
        return "".join(self._decoded_parts)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def streamed_token_count(self) -> int:
        return len(self._streamed_token_ids)

    def finalize(self) -> StreamingSession:
        source_text = "".join(self._source_parts)
        canonical = tuple(base_encode(source_text))
        streamed = tuple(self._streamed_token_ids)
        if self._decoded_parts:
            streamed_text = "".join(self._decoded_parts)
        else:
            streamed_text = "".join(base_decode(list(chunk.token_ids)) for chunk in self._chunks)
        text_mismatch_count = 0 if streamed_text == source_text else 1
        token_mismatch_count = 0 if streamed == canonical else 1
        return StreamingSession(
            source_text=source_text,
            chunk_size=self.chunk_size,
            chunks=tuple(self._chunks),
            streamed_text=streamed_text,
            streamed_token_ids=streamed,
            canonical_token_ids=canonical,
            text_mismatch_count=text_mismatch_count,
            token_mismatch_count=token_mismatch_count,
        )


def stream_encode(text: str, *, chunk_size: int = 64) -> list[list[int]]:
    encoder = StreamingEncoder(chunk_size=chunk_size)
    chunks = encoder.encode_text(text)
    return [list(chunk.token_ids) for chunk in chunks]


def stream_decode(token_chunks: Sequence[Iterable[int]]) -> str:
    decoder = StreamingEncoder()
    return decoder.decode_chunks(token_chunks)


def benchmark_streaming_latency(
    text: str,
    *,
    chunk_size: int = 128,
    iterations: int = 60,
    warmup: int = 6,
) -> dict[str, object]:
    payload = _coerce_text(text)
    _validate_chunk_size(chunk_size)
    if isinstance(iterations, bool) or not isinstance(iterations, int):
        raise TypeError("iterations must be int")
    if isinstance(warmup, bool) or not isinstance(warmup, int):
        raise TypeError("warmup must be int")
    if iterations <= 0:
        raise ValueError("iterations must be > 0")
    if warmup < 0:
        raise ValueError("warmup must be >= 0")

    text_chunks = split_text(payload, chunk_size=chunk_size)
    baseline_latencies: list[float] = []
    streaming_latencies: list[float] = []
    deterministic_hashes: list[str] = []
    mismatch_count = 0

    total_baseline_tokens = 0
    total_streaming_tokens = 0

    total_runs = warmup + iterations
    for run_index in range(total_runs):
        baseline_start = time.perf_counter()
        baseline_chunk_ids = [base_encode(chunk) for chunk in text_chunks]
        baseline_out = "".join(base_decode(ids) for ids in baseline_chunk_ids)
        baseline_elapsed = time.perf_counter() - baseline_start

        streaming_start = time.perf_counter()
        encoder = StreamingEncoder(chunk_size=chunk_size)
        streamed_chunks = encoder.encode_text(payload)
        streaming_out = encoder.decode_chunks([chunk.token_ids for chunk in streamed_chunks])
        streaming_elapsed = time.perf_counter() - streaming_start

        if run_index >= warmup:
            baseline_latencies.append(baseline_elapsed * 1000.0)
            streaming_latencies.append(streaming_elapsed * 1000.0)
            deterministic_hashes.append(sha256(streaming_out.encode("utf-8")).hexdigest())
            total_baseline_tokens += sum(len(ids) for ids in baseline_chunk_ids)
            total_streaming_tokens += sum(chunk.token_count for chunk in streamed_chunks)

        if baseline_out != payload or streaming_out != payload:
            mismatch_count += 1

    baseline_p50 = _percentile(baseline_latencies, 0.50)
    baseline_p95 = _percentile(baseline_latencies, 0.95)
    streaming_p50 = _percentile(streaming_latencies, 0.50)
    streaming_p95 = _percentile(streaming_latencies, 0.95)

    latency_ratio_p95 = (
        streaming_p95 / baseline_p95 if baseline_p95 > 0.0 else float("inf")
    )
    avg_streaming_seconds = (
        (sum(streaming_latencies) / len(streaming_latencies)) / 1000.0 if streaming_latencies else 0.0
    )
    throughput_tokens_per_sec = (
        total_streaming_tokens / (avg_streaming_seconds * len(streaming_latencies))
        if avg_streaming_seconds > 0.0 and streaming_latencies
        else 0.0
    )

    return {
        "chunk_size": chunk_size,
        "chunk_count": len(text_chunks),
        "iterations": iterations,
        "warmup": warmup,
        "baseline_latency_ms_p50": round(baseline_p50, 4),
        "baseline_latency_ms_p95": round(baseline_p95, 4),
        "streaming_latency_ms_p50": round(streaming_p50, 4),
        "streaming_latency_ms_p95": round(streaming_p95, 4),
        "latency_ratio_p95": round(latency_ratio_p95, 4),
        "throughput_tokens_per_sec": round(throughput_tokens_per_sec, 4),
        "baseline_token_count": total_baseline_tokens,
        "streaming_token_count": total_streaming_tokens,
        "mismatch_count": mismatch_count,
        "deterministic": mismatch_count == 0 and len(set(deterministic_hashes)) <= 1,
    }


__all__ = [
    "StreamingChunk",
    "StreamingSession",
    "StreamingEncoder",
    "benchmark_streaming_latency",
    "split_text",
    "stream_decode",
    "stream_encode",
]

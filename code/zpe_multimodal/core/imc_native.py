from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Sequence

from .codec import decode_with_bpe
from ..text.mapping_v1 import WORD_TO_CHAR

_MODALITY_NAMES = (
    "text",
    "diagram",
    "music",
    "voice",
    "image",
    "bpe",
    "mental",
    "touch",
    "smell",
    "taste",
)
_CHUNK_MODALITIES = ("diagram", "music", "voice", "image", "mental", "touch", "smell", "taste")


def _load_native_module() -> Any:
    for module_name in ("zpe_imc_kernel.zpe_imc_kernel", "zpe_imc_kernel"):
        try:
            return import_module(module_name)
        except Exception:
            continue
    raise RuntimeError("IMC Rust kernel native module is unavailable; build and install code/rust/imc_kernel first")


def _u32_view(raw: Any) -> memoryview:
    view = memoryview(raw)
    if view.format != "B":
        view = view.cast("B")
    if len(view) % 4 != 0:
        raise ValueError("native IMC payload length must be divisible by 4 bytes")
    return view.cast("I")


class KernelChunkStoreView(Mapping[str, tuple[memoryview, ...]]):
    def __init__(self, word_buffers: Mapping[str, memoryview], span_buffers: Mapping[str, memoryview]) -> None:
        self._word_buffers = dict(word_buffers)
        self._span_buffers = dict(span_buffers)
        self._cache: Dict[str, tuple[memoryview, ...]] = {}

    def __getitem__(self, key: str) -> tuple[memoryview, ...]:
        if key not in self._word_buffers:
            raise KeyError(key)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        words = self._word_buffers[key]
        spans = self._span_buffers[key]
        if len(spans) % 2 != 0:
            raise ValueError(f"native span payload for {key} has odd u32 count")
        chunks = tuple(words[int(spans[idx]) : int(spans[idx]) + int(spans[idx + 1])] for idx in range(0, len(spans), 2))
        self._cache[key] = chunks
        return chunks

    def __iter__(self) -> Iterator[str]:
        return iter(self._word_buffers)

    def __len__(self) -> int:
        return len(self._word_buffers)


_NATIVE = _load_native_module()
_CONFIGURED = False


def _ensure_configured() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _NATIVE.configure_normal_words(sorted(int(word) for word in WORD_TO_CHAR))
    _CONFIGURED = True


@dataclass(slots=True)
class KernelScan:
    counts: Dict[str, int]
    text_words: memoryview
    chunk_store: KernelChunkStoreView
    validation_errors: List[str]
    backend: Dict[str, Any] = field(default_factory=dict)


def _to_scan(payload: Mapping[str, Any]) -> KernelScan:
    counts_payload = list(payload["counts"])
    counts = {
        name: int(counts_payload[index]) if index < len(counts_payload) else 0
        for index, name in enumerate(_MODALITY_NAMES)
    }
    word_buffers = {name: _u32_view(payload[f"{name}_words_u32le"]) for name in _CHUNK_MODALITIES}
    span_buffers = {name: _u32_view(payload[f"{name}_spans_u32le"]) for name in _CHUNK_MODALITIES}
    return KernelScan(
        counts=counts,
        text_words=_u32_view(payload["text_words_u32le"]),
        chunk_store=KernelChunkStoreView(word_buffers, span_buffers),
        validation_errors=[str(error) for error in payload.get("validation_errors", [])],
        backend={
            "backend": str(payload.get("backend", "rust")),
            "origin": str(payload.get("origin", "pyo3_native_extension")),
            "native_backend": bool(payload.get("native_backend", True)),
            "fallback_used": bool(payload.get("fallback_used", False)),
            "payload_layout": str(payload.get("payload_layout", "")),
            "ffi_contract_version": str(payload.get("ffi_contract_version", "")),
            "build_profile": str(payload.get("build_profile", "")),
        },
    )


def scan_stream_kernel(stream: Sequence[object], record_invalid: bool = False) -> KernelScan:
    _ensure_configured()
    return _to_scan(_NATIVE.scan_stream(stream, record_invalid=record_invalid))


def scan_stream_batch_kernel(streams: Sequence[Sequence[object]], record_invalid: bool = False) -> List[KernelScan]:
    _ensure_configured()
    payloads = _NATIVE.scan_stream_batch(
        [[int(word) for word in stream] for stream in streams],
        record_invalid=record_invalid,
    )
    return [_to_scan(payload) for payload in payloads]


def encode_text_kernel(text: str) -> List[int]:
    _ensure_configured()
    return [int(word) for word in _NATIVE.encode_text(text)]


def encode_quadtree_kernel(image, threshold: float = 5.0, bit_depth: int = 3) -> tuple[List[int], Dict[str, int]]:
    import numpy as np

    _ensure_configured()
    arr = np.ascontiguousarray(image, dtype=np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("expected image shape (H, W, 3)")
    words, meta = _NATIVE.encode_quadtree(
        arr.tobytes(),
        int(arr.shape[1]),
        int(arr.shape[0]),
        int(bit_depth),
        float(threshold),
    )
    width, height, root, meta_bit_depth, threshold_x10 = meta
    return [int(word) for word in words], {
        "width": int(width),
        "height": int(height),
        "root": int(root),
        "bit_depth": int(meta_bit_depth),
        "threshold_x10": int(threshold_x10),
    }


def decode_quadtree_kernel(words: Sequence[int]):
    import numpy as np

    _ensure_configured()
    try:
        image_bytes, meta = _NATIVE.decode_quadtree(words)
    except TypeError:
        image_bytes, meta = _NATIVE.decode_quadtree([int(word) for word in words])
    width, height, root, bit_depth, threshold_x10 = meta
    array = np.frombuffer(image_bytes, dtype=np.uint8).reshape((int(height), int(width), 3))
    return array, {
        "width": int(width),
        "height": int(height),
        "root": int(root),
        "bit_depth": int(bit_depth),
        "threshold_x10": int(threshold_x10),
    }


def materialize_text_words(scan: KernelScan) -> List[int]:
    return [int(word) for word in scan.text_words]


def materialize_chunk_store(scan: KernelScan) -> Dict[str, List[List[int]]]:
    return {
        key: [[int(word) for word in chunk] for chunk in scan.chunk_store[key]]
        for key in scan.chunk_store
    }


def validate_stream_kernel(stream: Sequence[object]) -> tuple[bool, List[str]]:
    scan = scan_stream_kernel(stream, record_invalid=True)
    errors = list(scan.validation_errors)
    try:
        decode_with_bpe(scan.text_words)
    except Exception as exc:
        errors.append(str(exc))
    return len(errors) == 0, errors


def get_kernel_backend_info() -> Dict[str, Any]:
    _ensure_configured()
    info = dict(_NATIVE.backend_info())
    module_file = str(getattr(_NATIVE, "__file__", "") or "")
    module_name = str(getattr(_NATIVE, "__name__", "zpe_imc_kernel"))
    module_suffix = Path(module_file).suffix if module_file else ""
    info.update(
        {
            "backend": str(info.get("backend", "rust")),
            "origin": str(info.get("origin", "pyo3_native_extension")),
            "native": bool(info.get("native", True)),
            "fallback_used": bool(info.get("fallback_used", False)),
            "payload_layout": str(info.get("payload_layout", "")),
            "ffi_contract_version": str(info.get("ffi_contract_version", "")),
            "build_profile": str(info.get("build_profile", "")),
            "module_name": module_name,
            "module_file": module_file,
            "module_suffix": module_suffix,
            "compiled_extension": bool(module_suffix and module_suffix != ".py"),
            "adapter_module": __name__,
        }
    )
    return info

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import unicodedata

import pytest

from tests.common import configure_env

configure_env()

from zpe_multimodal import decode as api_decode
from zpe_multimodal import encode as api_encode
from zpe_multimodal.core.codec import decode as core_decode
from zpe_multimodal.core.codec import encode as core_encode

import source.core.codec as source_codec


CANONICAL_MATRIX_FIXTURES = [
    "hello",
    "Hello, ZPE IMC!",
    "ASCII punctuation []{}()<>!?.,;:'\"",
    "accents: café déjà fiancé naïve",
    "spanish: corazón niño acción",
    "french: où déjà été",
    "arabic: مرحبا بالعالم",
    "hindi: नमस्ते दुनिया",
    "japanese: 日本語の確認",
    "korean: 한국어 점검",
    "emoji simple: 🙂🚀🔥",
    "emoji sequence: 👩🏽\u200d💻👨🏿\u200d🔧",
]


@dataclass
class RuntimeSurface:
    name: str
    supported: bool
    runner: Callable[[str], tuple[list[int], str]] | None
    reason: str = ""
    enforce_token_parity: bool = True


def _nfd(text: str) -> str:
    return unicodedata.normalize("NFD", text)


def _coerce_ids(raw: object) -> list[int]:
    if isinstance(raw, dict) and "input_ids" in raw:
        raw = raw["input_ids"]
    if isinstance(raw, tuple):
        raw = list(raw)
    if isinstance(raw, list) and raw and isinstance(raw[0], list):
        raw = raw[0]
    if not isinstance(raw, list):
        raise TypeError(f"unsupported token id payload: {type(raw)!r}")
    return [int(v) for v in raw]


def _decode_from_adapter(adapter: object, token_ids: list[int]) -> str:
    if hasattr(adapter, "decode"):
        decode_fn = getattr(adapter, "decode")
        try:
            decoded = decode_fn(token_ids)
        except TypeError:
            decoded = decode_fn(token_ids, skip_special_tokens=True)
        return decoded.decode("utf-8", errors="replace") if isinstance(decoded, bytes) else str(decoded)

    if hasattr(adapter, "batch_decode"):
        batch_decode = getattr(adapter, "batch_decode")
        decoded = batch_decode([token_ids])[0]
        return decoded.decode("utf-8", errors="replace") if isinstance(decoded, bytes) else str(decoded)

    raise TypeError("adapter has no decode or batch_decode")


def _run_adapter(adapter: object, text: str) -> tuple[list[int], str]:
    if hasattr(adapter, "encode"):
        encode_fn = getattr(adapter, "encode")
        try:
            raw_ids = encode_fn(text)
        except TypeError:
            raw_ids = encode_fn(text, add_special_tokens=False)
    elif callable(adapter):
        raw_ids = adapter(text)
    else:
        raise TypeError("adapter is not callable and has no encode")

    ids = _coerce_ids(raw_ids)
    decoded = _decode_from_adapter(adapter, ids)
    return ids, _nfd(decoded)


def _load_optional_surfaces() -> list[RuntimeSurface]:
    optional: list[RuntimeSurface] = []

    try:
        from zpe_multimodal.adapters import as_huggingface, as_onnx, as_sentencepiece, as_tiktoken
    except Exception as exc:
        reason = f"optional adapters unavailable: {exc}"
        optional.extend(
            [
                RuntimeSurface(name="adapter_tiktoken", supported=False, runner=None, reason=reason),
                RuntimeSurface(name="adapter_huggingface", supported=False, runner=None, reason=reason),
                RuntimeSurface(name="adapter_sentencepiece", supported=False, runner=None, reason=reason),
                RuntimeSurface(name="adapter_onnx", supported=False, runner=None, reason=reason),
            ]
        )
        return optional

    factories = {
        "adapter_tiktoken": lambda: as_tiktoken(),
        "adapter_huggingface": lambda: as_huggingface(),
        "adapter_sentencepiece": lambda: as_sentencepiece(),
        "adapter_onnx": lambda: as_onnx(opset=18),
    }

    for name, factory in factories.items():
        try:
            adapter = factory()
            optional.append(
                RuntimeSurface(
                    name=name,
                    supported=True,
                    runner=lambda text, adapter=adapter: _run_adapter(adapter, text),
                    enforce_token_parity=False,
                )
            )
        except Exception as exc:
            optional.append(RuntimeSurface(name=name, supported=False, runner=None, reason=str(exc)))

    return optional


def _runtime_matrix() -> list[RuntimeSurface]:
    matrix = [
        RuntimeSurface(
            name="top_level_api",
            supported=True,
            runner=lambda text: (api_encode(text), _nfd(api_decode(api_encode(text)))),
        ),
        RuntimeSurface(
            name="core_codec",
            supported=True,
            runner=lambda text: (core_encode(text), _nfd(core_decode(core_encode(text)))),
        ),
        RuntimeSurface(
            name="source_compat",
            supported=True,
            runner=lambda text: (source_codec.encode(text), _nfd(source_codec.decode(source_codec.encode(text)))),
        ),
    ]
    matrix.extend(_load_optional_surfaces())
    return matrix


def test_adapter_parity_matrix_supported_surfaces_zero_mismatch() -> None:
    matrix = _runtime_matrix()
    baseline_surface = next(surface for surface in matrix if surface.name == "top_level_api")

    for text in CANONICAL_MATRIX_FIXTURES:
        baseline_ids, baseline_text = baseline_surface.runner(text)  # type: ignore[misc]

        for surface in matrix:
            if not surface.supported:
                continue
            assert surface.runner is not None
            ids, decoded = surface.runner(text)

            assert decoded == baseline_text, f"{surface.name} text parity mismatch for fixture: {text!r}"
            if surface.enforce_token_parity:
                assert ids == baseline_ids, f"{surface.name} token parity mismatch for fixture: {text!r}"


def test_adapter_parity_matrix_core_surfaces_present() -> None:
    matrix = _runtime_matrix()
    presence = {surface.name: surface.supported for surface in matrix}
    assert presence["top_level_api"] is True
    assert presence["core_codec"] is True
    assert presence["source_compat"] is True


@pytest.mark.parametrize("name", ["adapter_tiktoken", "adapter_huggingface", "adapter_sentencepiece", "adapter_onnx"])
def test_optional_adapter_surface_is_deterministically_reported(name: str) -> None:
    matrix = _runtime_matrix()
    selected = next(surface for surface in matrix if surface.name == name)
    if selected.supported:
        assert selected.runner is not None
    else:
        assert isinstance(selected.reason, str)
        assert selected.reason != ""

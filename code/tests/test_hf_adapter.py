from __future__ import annotations

import importlib.util

import pytest

from zpe_multimodal.adapters.huggingface import HuggingFaceZPEAdapter
from zpe_multimodal.adapters.huggingface import MissingOptionalDependencyError
from zpe_multimodal.adapters.huggingface import as_huggingface
from zpe_multimodal.adapters.huggingface import require_transformers


CANONICAL_FIXTURES = [
    "hello",
    "ASCII punctuation []{}()<>!?.,;:'\"",
    "accents: café déjà fiancé naïve",
    "emoji sequence: 👩🏽\u200d💻👨🏿\u200d🔧",
]


def test_as_huggingface_factory_returns_adapter() -> None:
    adapter = as_huggingface()
    assert isinstance(adapter, HuggingFaceZPEAdapter)


def test_adapter_encode_decode_parity_with_internal_roundtrip() -> None:
    adapter = HuggingFaceZPEAdapter()
    for text in CANONICAL_FIXTURES:
        ids = adapter.encode(text)
        assert isinstance(ids, list)
        assert all(isinstance(i, int) for i in ids)
        assert adapter.decode(ids) == text


def test_require_transformers_has_actionable_message_if_missing() -> None:
    if importlib.util.find_spec("transformers") is None:
        with pytest.raises(MissingOptionalDependencyError) as exc_info:
            require_transformers()
        msg = str(exc_info.value)
        assert "transformers" in msg
        assert ".[hf]" in msg
    else:
        require_transformers()


def test_torch_tensor_request_is_actionable_when_torch_missing() -> None:
    adapter = HuggingFaceZPEAdapter()
    try:
        payload = adapter("torch-check", return_tensors="pt")
    except MissingOptionalDependencyError as exc:
        assert "torch" in str(exc).lower()
    else:
        assert "input_ids" in payload
        assert "attention_mask" in payload


def test_invalid_return_tensors_value_raises() -> None:
    adapter = HuggingFaceZPEAdapter()
    with pytest.raises(ValueError):
        adapter("abc", return_tensors="tf")

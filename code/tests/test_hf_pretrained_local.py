from __future__ import annotations

from pathlib import Path

import pytest

from zpe_multimodal import ZPETokenizer
from zpe_multimodal import decode as base_decode
from zpe_multimodal import encode as base_encode
from zpe_multimodal.adapters.huggingface import HFTokenizerMetadata
from zpe_multimodal.adapters.huggingface import HuggingFaceZPEAdapter


CANONICAL_FIXTURES = [
    "hello",
    "Hello, ZPE IMC!",
    "emoji: 🙂🚀🔥",
    "mixed multilingual + emoji: Bonjour 世界 مرحبا 🙂",
]


def test_hf_local_save_and_from_pretrained_roundtrip(tmp_path: Path) -> None:
    metadata = HFTokenizerMetadata(
        ref="local-a2-roundtrip",
        extras={"owner": "A2", "contract": "hf-roundtrip"},
    )
    adapter = HuggingFaceZPEAdapter(metadata=metadata, model_max_length=8192)

    save_dir = tmp_path / "hf_tokenizer"
    saved = adapter.save_pretrained(save_dir)

    assert len(saved) == 3
    assert (save_dir / "tokenizer_config.json").exists()
    assert (save_dir / "special_tokens_map.json").exists()
    assert (save_dir / "zpe_tokenizer_config.json").exists()

    loaded = HuggingFaceZPEAdapter.from_pretrained(save_dir)
    assert loaded.model_max_length == 8192
    assert loaded.metadata.ref == "local-a2-roundtrip"
    assert loaded.metadata.extras["owner"] == "A2"

    for text in CANONICAL_FIXTURES:
        expected_ids = base_encode(text)
        expected_text = base_decode(expected_ids)

        assert loaded.encode(text) == expected_ids
        assert loaded.decode(expected_ids) == expected_text


def test_hf_call_numpy_tensors_shape(tmp_path: Path) -> None:
    adapter = HuggingFaceZPEAdapter()
    payload = adapter("shape-check", return_tensors="np")

    assert set(payload.keys()) == {"input_ids", "attention_mask"}
    assert payload["input_ids"].shape[0] == 1
    assert payload["attention_mask"].shape == payload["input_ids"].shape

    save_dir = tmp_path / "hf_tokenizer_np"
    adapter.save_pretrained(save_dir)
    loaded = HuggingFaceZPEAdapter.from_pretrained(save_dir)
    assert loaded.decode(loaded.encode("shape-check")) == "shape-check"


def test_hf_from_pretrained_missing_local_path_raises() -> None:
    missing = Path("/tmp") / "zpe-a2-this-should-not-exist"
    if missing.exists():
        pytest.skip("cannot assert missing-path behavior because fixture path exists")
    with pytest.raises(FileNotFoundError, match="Local pretrained path not found"):
        HuggingFaceZPEAdapter.from_pretrained(missing, local_files_only=True)


def test_hf_roundtrip_preserves_lattice_metadata(tmp_path: Path) -> None:
    lattice = tmp_path / "example_a2.lattice"
    lattice.write_text("zpe-lattice-metadata", encoding="utf-8")

    adapter = HuggingFaceZPEAdapter(tokenizer=ZPETokenizer.from_lattice(str(lattice)))
    save_dir = tmp_path / "hf_lattice_roundtrip"
    adapter.save_pretrained(save_dir)

    loaded = HuggingFaceZPEAdapter.from_pretrained(save_dir)
    assert loaded.metadata.lattice_path is not None
    assert loaded.tokenizer.lattice_path == str(lattice.resolve())

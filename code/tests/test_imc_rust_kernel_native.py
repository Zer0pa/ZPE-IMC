from __future__ import annotations

from array import array
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import configure_env

configure_env()

from source.core.constants import WORD_MASK
from source.core.codec import _encode_noemoji_python
from source.core.imc import IMCDecoder, IMCEncoder, get_kernel_backend_info, validate_stream
from source.core.imc_native import (
    decode_quadtree_kernel,
    encode_quadtree_kernel,
    encode_text_kernel,
    materialize_text_words,
    scan_stream_batch_kernel,
    scan_stream_kernel,
)
from source.image.quadtree_enhanced_codec import IMAGE_FAMILY_VALUE, decode_enhanced_payloads, encode_enhanced


def test_rust_kernel_backend_reports_compiled_native_extension() -> None:
    info = get_kernel_backend_info()

    assert info["backend"] == "rust"
    assert info["native"] is True
    assert info["fallback_used"] is False
    assert info["compiled_extension"] is True
    assert info["payload_layout"] == "u32le_bytes+spans_v1"
    assert info["ffi_contract_version"] == "imc_flat_u32le_v1"
    assert info["build_profile"] == "release"
    assert info["allocator"] == "mimalloc"
    assert info["scan_fast_path"] == "u32_sequence_extract_v1"
    assert info["text_encoder"] == "rust_nfd_phf_v1"
    assert info["image_encoder"] == "rust_prefix_quadtree_v1"
    assert info["image_decoder"] == "rust_enhanced_quadtree_v1"
    assert info["module_file"]
    assert Path(str(info["module_file"])).suffix != ".py"


def test_native_scan_exposes_flat_word_buffer_views() -> None:
    stream = IMCEncoder(require_env=False).add_text("flat native payload").add_bpe([7, 8]).build()
    scan = scan_stream_kernel(stream, record_invalid=True)

    assert isinstance(scan.text_words, memoryview)
    assert materialize_text_words(scan) == [int(word) for word in scan.text_words]
    assert scan.backend["payload_layout"] == "u32le_bytes+spans_v1"
    assert scan.backend["ffi_contract_version"] == "imc_flat_u32le_v1"


def test_decoder_uses_native_rust_backend_without_python_scan_fallback() -> None:
    stream = IMCEncoder(require_env=False).add_text("rust-backed canonical path").add_bpe([1, 2, 3]).build()
    result = IMCDecoder().decode(stream)
    info = get_kernel_backend_info()

    assert result.stream_valid is True
    assert result.text == "rust-backed canonical path"
    assert result.bpe_tokens == [1, 2, 3]
    assert info["backend"] == "rust"
    assert info["fallback_used"] is False


def test_decoder_accepts_buffer_backed_u32_input() -> None:
    stream = IMCEncoder(require_env=False).add_text("buffer-backed native path").add_bpe([9, 10]).build()
    buffer_stream = memoryview(array("I", stream))

    scan = scan_stream_kernel(buffer_stream)
    result = IMCDecoder().decode(buffer_stream)

    assert materialize_text_words(scan) == stream
    assert result.stream_valid is True
    assert result.text == "buffer-backed native path"
    assert result.bpe_tokens == [9, 10]


def test_validate_stream_surfaces_unknown_unit_word_via_native_scan_path() -> None:
    stream = IMCEncoder(require_env=False).add_text("native validate").build()
    stream.insert(1, 0)

    valid, errors = validate_stream(stream)

    assert valid is False
    assert any("unknown unit word" in error for error in errors)


def test_native_scan_reports_out_of_range_u32_without_prevalidation_pass() -> None:
    stream = [WORD_MASK + 1, *IMCEncoder(require_env=False).add_text("range check").build()]

    scan = scan_stream_kernel(stream, record_invalid=True)

    assert any("word out of range" in error for error in scan.validation_errors)


def test_native_text_encoder_matches_python_nfd_escape_path() -> None:
    text = "Cre\u0301me bru\u0302le\u0301e 🙂 Œuvre"

    assert encode_text_kernel(text) == _encode_noemoji_python(text)


def test_native_quadtree_encoder_returns_words_and_meta() -> None:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[:, :, 0] = np.arange(8, dtype=np.uint8) * 32

    words, meta = encode_quadtree_kernel(image, threshold=5.0, bit_depth=3)

    assert words
    assert meta["width"] == 8
    assert meta["height"] == 8
    assert meta["root"] == 8
    assert meta["bit_depth"] == 3


def test_native_quadtree_decoder_matches_python_payload_decoder() -> None:
    image = np.zeros((16, 16, 3), dtype=np.uint8)
    image[:, :, 0] = np.arange(16, dtype=np.uint8) * 17
    image[:, :, 1] = np.arange(16, dtype=np.uint8).reshape(16, 1) * 11
    image[:, :, 2] = (image[:, :, 0] // 2) + (image[:, :, 1] // 3)
    words, _ = encode_enhanced(image, threshold=5.0, bit_depth=3)

    native_image, native_meta = decode_quadtree_kernel(words)
    payloads = [
        int(word) & 0xFFFF
        for word in words
        if ((int(word) >> 18) & 0x3) == 2
        and ((int(word) >> 16) & 0x3) == 0
        and ((int(word) & 0x0C00) == IMAGE_FAMILY_VALUE)
    ]
    python_image, python_meta = decode_enhanced_payloads(payloads)

    np.testing.assert_array_equal(native_image, python_image)
    assert native_meta["width"] == python_meta.width
    assert native_meta["height"] == python_meta.height
    assert native_meta["root"] == python_meta.root
    assert native_meta["bit_depth"] == python_meta.bit_depth
    assert native_meta["threshold_x10"] == python_meta.threshold_x10


def test_native_scan_batch_preserves_input_order() -> None:
    stream_a = IMCEncoder(require_env=False).add_text("alpha").build()
    stream_b = IMCEncoder(require_env=False).add_text("beta").add_bpe([4, 5]).build()

    scans = scan_stream_batch_kernel([stream_a, stream_b])

    assert len(scans) == 2
    assert materialize_text_words(scans[0]) == stream_a
    assert materialize_text_words(scans[1]) == stream_b

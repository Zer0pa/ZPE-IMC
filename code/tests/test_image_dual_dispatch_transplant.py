from __future__ import annotations

import numpy as np
import pytest

from tests.common import configure_env

configure_env()

import source.core.imc as _imc  # noqa: F401
from source.image.dual_dispatch import decode_image_words, detect_family
from source.image.quadtree_enhanced_codec import encode_enhanced
from source.image.quadtree_legacy_codec import encode_legacy


def test_detect_family_rejects_mixed_markers() -> None:
    rgb = np.zeros((4, 4, 3), dtype=np.uint8)
    legacy_input = np.zeros((4, 4, 3), dtype=np.uint8)
    enhanced_words, _ = encode_enhanced(rgb, threshold=5.0, bit_depth=3)
    legacy_words, _ = encode_legacy(legacy_input, threshold=5.0)
    mixed = [enhanced_words[0], legacy_words[0]]
    with pytest.raises(ValueError, match="mixed image family markers"):
        detect_family(mixed)


def test_decode_image_words_still_decodes_enhanced() -> None:
    rgb = np.zeros((4, 4, 3), dtype=np.uint8)
    enhanced_words, _ = encode_enhanced(rgb, threshold=5.0, bit_depth=3)
    decoded = decode_image_words(enhanced_words)
    assert decoded.mode == "enhanced"
    assert decoded.image.shape == rgb.shape


def test_decode_image_words_rejects_truncated_enhanced_stream() -> None:
    rgb = np.zeros((4, 4, 3), dtype=np.uint8)
    enhanced_words, _ = encode_enhanced(rgb, threshold=5.0, bit_depth=3)
    truncated = enhanced_words[:-1]
    with pytest.raises(ValueError, match="invalid enhanced stream"):
        decode_image_words(truncated)

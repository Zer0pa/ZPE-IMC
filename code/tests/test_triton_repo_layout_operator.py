from __future__ import annotations

from pathlib import Path

import pytest


CODE_ROOT = Path(__file__).resolve().parents[1]
TRITON_TOKENIZER_MODEL = (
    CODE_ROOT / "deployment" / "triton" / "model_repository" / "zpe_tokenizer_onnx" / "1" / "model.onnx"
)
A6_TOKENIZER_EXPORT = (
    CODE_ROOT.parent
    / "proofs"
    / "artifacts"
    / "2026-02-24_program_maximal"
    / "A6"
    / "exported"
    / "zpe_tokenizer_op.onnx"
)
SKIP_REASON = "A6 export artifact is excluded from the public snapshot; operator/private byte-identity check skipped"


def _private_a6_export_available() -> bool:
    return A6_TOKENIZER_EXPORT.is_file()


@pytest.mark.skipif(
    not _private_a6_export_available(),
    reason=SKIP_REASON,
)
def test_triton_tokenizer_model_matches_private_a6_export_artifact() -> None:
    assert TRITON_TOKENIZER_MODEL.is_file()
    assert _private_a6_export_available()
    assert TRITON_TOKENIZER_MODEL.read_bytes() == A6_TOKENIZER_EXPORT.read_bytes()

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


@pytest.mark.skipif(
    not A6_TOKENIZER_EXPORT.exists(),
    reason="A6 export artifact is excluded from the public snapshot; operator/private byte-identity check skipped",
)
def test_triton_tokenizer_model_matches_private_a6_export_artifact() -> None:
    assert TRITON_TOKENIZER_MODEL.exists()
    assert A6_TOKENIZER_EXPORT.exists()
    assert TRITON_TOKENIZER_MODEL.read_bytes() == A6_TOKENIZER_EXPORT.read_bytes()

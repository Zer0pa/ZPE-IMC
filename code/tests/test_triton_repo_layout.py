from __future__ import annotations

from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
TRITON_REPO = CODE_ROOT / "deployment" / "triton" / "model_repository"


def test_triton_model_repository_layout_exists() -> None:
    required_files = [
        TRITON_REPO / "README.md",
        TRITON_REPO / "zpe_tokenizer_onnx" / "config.pbtxt",
        TRITON_REPO / "zpe_tokenizer_onnx" / "1" / "model.onnx",
        TRITON_REPO / "zpe_token_passthrough" / "config.pbtxt",
        TRITON_REPO / "zpe_token_passthrough" / "1" / "model.py",
        TRITON_REPO / "zpe_tokenizer_ensemble" / "config.pbtxt",
    ]
    for path in required_files:
        assert path.exists(), f"missing required Triton artifact: {path}"


def test_triton_model_version_directories_are_numeric() -> None:
    for model_name in ("zpe_tokenizer_onnx", "zpe_token_passthrough", "zpe_tokenizer_ensemble"):
        version_dir = TRITON_REPO / model_name / "1"
        assert version_dir.exists(), f"missing version directory for {model_name}"
        assert version_dir.is_dir()
        assert version_dir.name.isdigit()


def test_triton_tokenizer_model_matches_a6_export_artifact() -> None:
    triton_model = TRITON_REPO / "zpe_tokenizer_onnx" / "1" / "model.onnx"
    assert triton_model.exists()
    assert triton_model.stat().st_size > 0

    a6_model = (
        CODE_ROOT.parent
        / "proofs"
        / "artifacts"
        / "2026-02-24_program_maximal"
        / "A6"
        / "exported"
        / "zpe_tokenizer_op.onnx"
    )
    assert a6_model.exists()
    assert triton_model.read_bytes() == a6_model.read_bytes()


def test_triton_passthrough_backend_has_required_entrypoints() -> None:
    model_py = TRITON_REPO / "zpe_token_passthrough" / "1" / "model.py"
    payload = model_py.read_text(encoding="utf-8")
    assert "class TritonPythonModel" in payload
    assert "def execute(" in payload

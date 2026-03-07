from __future__ import annotations

from pathlib import Path
import re


CODE_ROOT = Path(__file__).resolve().parents[1]
TRITON_REPO = CODE_ROOT / "deployment" / "triton" / "model_repository"


def _assert_contains(payload: str, pattern: str) -> None:
    assert re.search(pattern, payload, flags=re.MULTILINE), f"pattern not found: {pattern}"


def test_tokenizer_onnx_config_contract() -> None:
    config = (TRITON_REPO / "zpe_tokenizer_onnx" / "config.pbtxt").read_text(encoding="utf-8")
    _assert_contains(config, r'name:\s*"zpe_tokenizer_onnx"')
    _assert_contains(config, r'backend:\s*"onnxruntime"')
    _assert_contains(config, r'name:\s*"input_text"')
    _assert_contains(config, r'data_type:\s*TYPE_STRING')
    _assert_contains(config, r'name:\s*"token_ids"')
    _assert_contains(config, r'data_type:\s*TYPE_INT64')


def test_passthrough_config_contract() -> None:
    config = (TRITON_REPO / "zpe_token_passthrough" / "config.pbtxt").read_text(encoding="utf-8")
    _assert_contains(config, r'name:\s*"zpe_token_passthrough"')
    _assert_contains(config, r'backend:\s*"python"')
    _assert_contains(config, r'name:\s*"token_ids"')
    _assert_contains(config, r'name:\s*"token_ids_out"')


def test_ensemble_config_wires_tokenizer_to_downstream_step() -> None:
    config = (TRITON_REPO / "zpe_tokenizer_ensemble" / "config.pbtxt").read_text(encoding="utf-8")
    _assert_contains(config, r'name:\s*"zpe_tokenizer_ensemble"')
    _assert_contains(config, r'platform:\s*"ensemble"')
    _assert_contains(config, r'model_name:\s*"zpe_tokenizer_onnx"')
    _assert_contains(config, r'model_name:\s*"zpe_token_passthrough"')
    _assert_contains(config, r'key:\s*"input_text"\s+value:\s*"INPUT_TEXT"')
    _assert_contains(config, r'key:\s*"token_ids"\s+value:\s*"TOKEN_IDS_RAW"')
    _assert_contains(config, r'key:\s*"token_ids_out"\s+value:\s*"TOKEN_IDS"')

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from tests.common import configure_env

configure_env()

from zpe_multimodal.core.imc import IMCDecoder, IMCEncoder

ROOT = Path(__file__).resolve().parents[1]
V0_ROOT = ROOT.parent
EXECUTABLE_DEMO = V0_ROOT / "executable" / "demo.py"


def _runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("STROKEGRAM_ENABLE_DIAGRAM", "1")
    env.setdefault("STROKEGRAM_ENABLE_MUSIC", "1")
    env.setdefault("STROKEGRAM_ENABLE_VOICE", "1")
    return env


def _run_cli_demo() -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-m", "zpe_multimodal.cli", "demo", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=_runtime_env(),
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip())


def _run_executable_demo_stdout() -> str:
    proc = subprocess.run(
        [sys.executable, str(EXECUTABLE_DEMO)],
        cwd=V0_ROOT,
        text=True,
        capture_output=True,
        env=_runtime_env(),
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _extract_labeled_json(output: str, label: str) -> dict[str, object]:
    lines = output.splitlines()
    assert label in lines, f"missing label {label!r} in executable output"
    index = lines.index(label)
    assert index + 1 < len(lines), f"missing JSON payload after {label!r}"
    return json.loads(lines[index + 1].strip())


def test_c01_sentinel_plain_text_does_not_spoof_bpe_tokens() -> None:
    text = "plain text with sentinel \ufffe1A\ufffe should not spoof"
    stream = IMCEncoder(require_env=False).add_text(text).build()
    result = IMCDecoder().decode(stream)
    assert result.text == text
    assert result.bpe_tokens == []
    assert result.stream_valid is True


def test_c02_mixed_type_dirty_stream_returns_structured_errors_no_uncaught_crash() -> None:
    stream = IMCEncoder(require_env=False).add_text("dirty-data").add_bpe([1, 2, 3]).build()
    stream[1:1] = [0, "bad", -1, 2**30, {"x": 1}]

    result = IMCDecoder().decode(stream)

    assert result.stream_valid is False
    assert isinstance(result.validation_errors, list)
    assert result.validation_errors
    assert any("text_decode_error" in err or "index " in err for err in result.validation_errors)


def test_c03_cli_and_executable_demo_total_word_parity() -> None:
    cli_payload = _run_cli_demo()
    executable_out = _run_executable_demo_stdout()
    executable_summary = _extract_labeled_json(executable_out, "STREAM_SUMMARY")

    assert cli_payload["total_words"] == executable_summary["total_words"]
    assert cli_payload["modality_counts"] == executable_summary["counts"]


def test_c05_voice_capability_mode_is_explicit_in_runtime_outputs() -> None:
    cli_payload = _run_cli_demo()
    executable_out = _run_executable_demo_stdout()
    executable_mode_payload = _extract_labeled_json(executable_out, "VOICE_CAPABILITY_MODE")

    cli_mode = cli_payload.get("voice_capability_mode")
    executable_mode = executable_mode_payload.get("voice_capability_mode")
    assert cli_mode in {"full", "fallback"}
    assert executable_mode in {"full", "fallback"}
    assert cli_mode == executable_mode

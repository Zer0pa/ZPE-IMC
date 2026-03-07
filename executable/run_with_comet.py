#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
from typing import Any

from determinism_probe import PROBE_ID, run_probe

SCRIPT_PATH = Path(__file__).resolve()
V0_ROOT = SCRIPT_PATH.parents[1]
CODE_ROOT = V0_ROOT / "code"
LOG_ROOT = V0_ROOT / "proofs" / "logs"
BENCHMARK_ARTIFACT_ROOT = CODE_ROOT / "benchmarks" / "artifacts"
BENCHMARK_METRICS_DIR = BENCHMARK_ARTIFACT_ROOT / "metrics"
BENCHMARK_TELEMETRY = BENCHMARK_ARTIFACT_ROOT / "telemetry" / "progressive_events.jsonl"
BENCHMARK_REPORT_PATH = BENCHMARK_ARTIFACT_ROOT / "BENCHMARK_REPORT.md"
HOTSPOT_PROFILE_PATH = BENCHMARK_ARTIFACT_ROOT / "HOTSPOT_PROFILE.md"
PROOF_MANIFEST_PATH = LOG_ROOT / "phase6_run_of_record_manifest.json"

DEFAULT_WORKSPACE = "zer0pa"
DEFAULT_CLASSIC_PROJECT = "ZPE-IMC-Performance"
DEFAULT_OPIK_PROJECT = "ZPE-IMC-Canonical"
DEFAULT_OPIK_URL = "https://www.comet.com/opik/api"
DEFAULT_THREAD_ID = "imc-closure-wave1"

BENCHMARK_SCALAR_KEYS = (
    "latency_ms_p50",
    "latency_ms_p95",
    "peak_memory_mb",
    "throughput_tokens_per_sec",
)
CANONICAL_MODALITIES = (
    "text",
    "diagram",
    "music",
    "voice",
    "image",
    "bpe",
    "mental",
    "touch",
    "smell",
    "taste",
)
MODE_ORDER = ("normal", "escape", "extension", "reserved")
CURATED_METRIC_PREFIX = "zpe_imc_e2e"
CURATED_HISTORY_LOOKBACK = 8
CURATED_INRUN_CHECKPOINTS = 48
TRANSPORT_RESERVED_SHARE_THRESHOLD = 0.02
TRANSPORT_THROUGHPUT_TARGET_WPS = 800.0
CANONICAL_PARALLEL_MIN_TOTAL_WORDS = 1_350_000
CANONICAL_PARALLEL_MAX_BATCH_ITERATIONS = 512
CANONICAL_PREPASS_MEASUREMENT_MODE = "single_stream_single_process"
CANONICAL_STEADY_STATE_MEASUREMENT_MODE = "steady_state_parallel_batch"

if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))


@dataclass
class ProjectCheck:
    target: str
    status: str
    resolved_name: str | None = None
    resolved_id: str | None = None
    resolved_slug: str | None = None
    url: str | None = None
    handshake_error: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    label: str
    returncode: int
    output: str


@dataclass
class CanonicalRunResult:
    summary: dict[str, Any]
    reran_for_cpu_saturation: bool
    rerun_workers: int


@dataclass
class AttachmentUploadResult:
    status: str
    requested_count: int
    uploaded_count: int
    verified_count: int
    requested_paths: list[str] = field(default_factory=list)
    uploaded_paths: list[str] = field(default_factory=list)
    skipped_paths: list[str] = field(default_factory=list)
    verification_items: list[str] = field(default_factory=list)
    error: str | None = None
    verification_error: str | None = None


@dataclass
class CuratedMetricSurface:
    final_metrics: dict[str, float]
    inrun_series: dict[str, list[tuple[int, float]]]
    cross_run_series: dict[str, list[tuple[int, float]]]
    benchmark_series: dict[str, list[tuple[int, float]]]
    parameter_values: dict[str, Any]
    metric_names: list[str]


class ClassicCometAdapter:
    def __init__(self, experiment: Any | None, notes: list[str]) -> None:
        self.experiment = experiment
        self.notes = notes

    @property
    def enabled(self) -> bool:
        return self.experiment is not None

    @classmethod
    def create(
        cls,
        *,
        project_check: ProjectCheck,
        workspace: str,
        run_name: str,
        disabled: bool,
    ) -> "ClassicCometAdapter":
        notes: list[str] = []
        if disabled:
            notes.append("classic Comet adapter disabled by flag")
            return cls(None, notes)
        if project_check.status not in {"EXISTS", "CREATED"}:
            notes.append(f"classic Comet adapter inactive: {project_check.handshake_error or 'project check did not pass'}")
            return cls(None, notes)

        try:
            from comet_ml import Experiment  # type: ignore
        except Exception as exc:
            notes.append(f"classic Comet adapter unavailable: {exc}")
            return cls(None, notes)

        try:
            experiment = Experiment(
                api_key=os.environ.get("COMET_API_KEY") or None,
                workspace=workspace,
                project_name=project_check.resolved_name or DEFAULT_CLASSIC_PROJECT,
                log_code=False,
                log_graph=False,
                auto_param_logging=False,
                auto_metric_logging=False,
                parse_args=False,
                auto_output_logging=None,
                log_env_details=False,
                log_git_metadata=False,
                log_git_patch=False,
                disabled=False,
                log_env_gpu=False,
                log_env_host=False,
                display_summary=False,
                log_env_cpu=False,
                log_env_network=False,
                log_env_disk=False,
                auto_log_co2=False,
            )
            experiment.set_name(run_name)
            notes.append("classic Comet metrics logging enabled")
            return cls(experiment, notes)
        except Exception as exc:
            notes.append(f"classic Comet adapter failed to initialize: {type(exc).__name__}: {exc}")
            return cls(None, notes)

    def log_metrics(self, metrics: dict[str, int | float]) -> None:
        if self.experiment is None:
            return
        self.experiment.log_metrics(metrics)

    def log_metric(self, name: str, value: int | float, *, step: int | None = None) -> None:
        if self.experiment is None:
            return
        if step is None:
            self.experiment.log_metric(name, value)
            return
        self.experiment.log_metric(name, value, step=step)

    def log_parameter(self, name: str, value: Any) -> None:
        if self.experiment is None:
            return
        self.experiment.log_parameter(name, value)

    def log_text(self, text: str) -> None:
        if self.experiment is None:
            return
        self.experiment.log_text(text)

    def identity(self) -> dict[str, str]:
        if self.experiment is None:
            return {"experiment_key": "", "experiment_url": ""}
        experiment_key = ""
        experiment_url = ""
        try:
            experiment_key = str(self.experiment.get_key() or "")
        except Exception:
            pass
        try:
            experiment_url = str(getattr(self.experiment, "url", "") or "")
        except Exception:
            pass
        return {"experiment_key": experiment_key, "experiment_url": experiment_url}

    def finish(self) -> dict[str, str]:
        identity = self.identity()
        if self.experiment is None:
            return identity
        self.experiment.end()
        return identity


class OpikAdapter:
    def __init__(self, client: Any | None, notes: list[str]) -> None:
        self.client = client
        self.notes = notes

    @property
    def enabled(self) -> bool:
        return self.client is not None

    @classmethod
    def create(
        cls,
        *,
        project_check: ProjectCheck,
        workspace: str,
        disabled: bool,
    ) -> "OpikAdapter":
        notes: list[str] = []
        if disabled:
            notes.append("Opik adapter disabled by flag")
            return cls(None, notes)
        if project_check.status not in {"EXISTS", "CREATED"}:
            notes.append(f"Opik adapter inactive: {project_check.handshake_error or 'project check did not pass'}")
            return cls(None, notes)

        try:
            from opik import Opik  # type: ignore
        except Exception as exc:
            notes.append(f"Opik adapter unavailable: {exc}")
            return cls(None, notes)

        try:
            client = Opik(
                project_name=project_check.resolved_name or DEFAULT_OPIK_PROJECT,
                workspace=workspace,
                host=os.environ.get("OPIK_URL_OVERRIDE", DEFAULT_OPIK_URL),
                api_key=_opik_api_key() or None,
                _use_batching=True,
                _show_misconfiguration_message=False,
            )
            notes.append("Opik trace logging enabled")
            return cls(client, notes)
        except Exception as exc:
            notes.append(f"Opik adapter failed to initialize: {type(exc).__name__}: {exc}")
            return cls(None, notes)

    def start_trace(self, *, name: str, metadata: dict[str, Any], input_payload: dict[str, Any]) -> Any | None:
        if self.client is None:
            return None
        return self.client.trace(
            name=name,
            project_name=self.client.project_name,
            metadata=metadata,
            input=input_payload,
            thread_id=DEFAULT_THREAD_ID,
        )

    def finish(self) -> None:
        if self.client is None:
            return
        self.client.flush()
        self.client.end()

    def get_trace_url(self, trace_id: str) -> str:
        if self.client is None or not trace_id:
            return ""
        try:
            from opik.api_objects import opik_client  # type: ignore

            return str(
                opik_client.url_helpers.get_project_url_by_trace_id(  # type: ignore[attr-defined]
                    trace_id=trace_id,
                    url_override=self.client._config.url_override,
                )
            )
        except Exception as exc:
            self.notes.append(f"Opik trace URL resolution unavailable: {type(exc).__name__}: {exc}")
            return ""

    def upload_attachments(self, *, entity_type: str, entity_id: str, paths: list[Path]) -> AttachmentUploadResult:
        requested_paths = [str(path) for path in paths]
        if self.client is None or not entity_id:
            return AttachmentUploadResult(
                status="disabled",
                requested_count=0,
                uploaded_count=0,
                verified_count=0,
                requested_paths=requested_paths,
            )

        existing_paths: list[Path] = []
        skipped_paths: list[str] = []
        for path in paths:
            if path.exists():
                existing_paths.append(path)
            else:
                skipped_paths.append(str(path))

        if not existing_paths:
            return AttachmentUploadResult(
                status="skipped",
                requested_count=0,
                uploaded_count=0,
                verified_count=0,
                requested_paths=requested_paths,
                skipped_paths=skipped_paths,
            )

        try:
            self.client.flush()
        except Exception:
            pass

        uploaded_paths: list[str] = []
        verification_items: list[str] = []
        errors: list[str] = []
        verification_error: str | None = None
        try:
            attachment_client = self.client.get_attachment_client()
            project_name = str(self.client.project_name)
            for path in existing_paths:
                try:
                    attachment_client.upload_attachment(
                        project_name=project_name,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        file_path=str(path),
                    )
                    uploaded_paths.append(str(path))
                except Exception as exc:
                    errors.append(f"{path.name}: {type(exc).__name__}: {exc}")
            try:
                attachments = attachment_client.get_attachment_list(
                    project_name=project_name,
                    entity_id=entity_id,
                    entity_type=entity_type,
                )
                verification_items = [
                    str(
                        getattr(item, "file_name", None)
                        or getattr(item, "name", None)
                        or getattr(item, "id", "")
                    )
                    for item in attachments
                ]
            except Exception as exc:
                verification_error = f"{type(exc).__name__}: {exc}"
        except Exception as exc:
            self.notes.append(f"Opik native attachment upload unavailable: {type(exc).__name__}: {exc}")
            return AttachmentUploadResult(
                status="fallback_reference_only",
                requested_count=len(existing_paths),
                uploaded_count=0,
                verified_count=0,
                requested_paths=requested_paths,
                skipped_paths=skipped_paths,
                error=f"{type(exc).__name__}: {exc}",
            )

        verified_count = len(verification_items)
        status = "verified"
        if errors:
            status = "partial_failure"
        elif verification_error is not None:
            status = "uploaded_unverified"
        elif uploaded_paths and verified_count < len(uploaded_paths):
            status = "uploaded_unverified"

        if status != "verified":
            self.notes.append(
                f"Opik attachment upload status for {entity_type}:{entity_id} = {status}"
            )

        return AttachmentUploadResult(
            status=status,
            requested_count=len(existing_paths),
            uploaded_count=len(uploaded_paths),
            verified_count=verified_count,
            requested_paths=requested_paths,
            uploaded_paths=uploaded_paths,
            skipped_paths=skipped_paths,
            verification_items=verification_items,
            error="; ".join(errors) if errors else None,
            verification_error=verification_error,
        )


def _with_code_pythonpath(env: dict[str, str]) -> dict[str, str]:
    updated = env.copy()
    existing_pythonpath = updated.get("PYTHONPATH", "")
    if existing_pythonpath:
        updated["PYTHONPATH"] = f"{CODE_ROOT}:{existing_pythonpath}"
    else:
        updated["PYTHONPATH"] = str(CODE_ROOT)
    return updated


def _runtime_env() -> dict[str, str]:
    env = _with_code_pythonpath(os.environ)
    env["STROKEGRAM_ENABLE_DIAGRAM"] = "1"
    env["STROKEGRAM_ENABLE_MUSIC"] = "1"
    env["STROKEGRAM_ENABLE_VOICE"] = "1"
    return env


def _subprocess_env() -> dict[str, str]:
    env = _runtime_env()
    for key in list(env):
        if key.startswith("COMET_") or key.startswith("OPIK_"):
            env.pop(key, None)
    return env


def _opik_api_key() -> str:
    return (os.environ.get("OPIK_API_KEY") or os.environ.get("COMET_API_KEY") or "").strip()


def _opik_api_key_source() -> str:
    if (os.environ.get("OPIK_API_KEY") or "").strip():
        return "OPIK_API_KEY"
    if (os.environ.get("COMET_API_KEY") or "").strip():
        return "COMET_API_KEY_FALLBACK"
    return "(unset)"


def _remote_logging_enabled(*, enable: bool, disable: bool) -> bool:
    return bool(enable and not disable)


def _disabled_project_check(target: str, reason: str) -> ProjectCheck:
    return ProjectCheck(target=target, status="DISABLED", handshake_error=reason)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run promoted IMC validation with local proof artifacts by default; opt in to live logging explicitly."
    )
    parser.add_argument("--env-check-out", type=Path, default=LOG_ROOT / "phase6_comet_env_check.txt")
    parser.add_argument("--log-out", type=Path, default=LOG_ROOT / "phase6_comet_run.txt")
    parser.add_argument(
        "--enable-classic-comet",
        action="store_true",
        help="Opt in to classic Comet metrics logging. Release-default behavior is local-only.",
    )
    parser.add_argument(
        "--enable-opik",
        action="store_true",
        help="Opt in to Opik trace logging. Release-default behavior is local-only.",
    )
    parser.add_argument(
        "--disable-classic-comet",
        action="store_true",
        help="Force-disable classic Comet metrics logging even if explicitly enabled.",
    )
    parser.add_argument(
        "--disable-opik",
        action="store_true",
        help="Force-disable Opik trace logging even if explicitly enabled.",
    )
    parser.add_argument(
        "--benchmark-profile",
        choices=("all", "baseline", "medium", "heavy"),
        default="all",
        help="Benchmark profile to run inside the wrapper.",
    )
    return parser.parse_args()


def _trim_output(text: str, lines: int = 40) -> str:
    return "\n".join(text.splitlines()[:lines])


def _run_command(*, label: str, cmd: list[str], cwd: Path, env: dict[str, str]) -> CommandResult:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    output = (proc.stdout or "") + (proc.stderr or "")
    return CommandResult(label=label, returncode=proc.returncode, output=output)


def _parse_pytest_counts(text: str) -> dict[str, int]:
    counts = {"tests_total": 0, "tests_passed": 0, "tests_failed": 0}
    patterns = {
        "tests_passed": re.compile(r"(?<!\w)(\d+)\s+passed\b"),
        "failed": re.compile(r"(?<!\w)(\d+)\s+failed\b"),
        "errors": re.compile(r"(?<!\w)(\d+)\s+errors?\b"),
    }
    for line in text.splitlines():
        passed_match = patterns["tests_passed"].search(line)
        if passed_match is not None:
            counts["tests_passed"] = max(counts["tests_passed"], int(passed_match.group(1)))
        failed_match = patterns["failed"].search(line)
        if failed_match is not None:
            counts["tests_failed"] += int(failed_match.group(1))
        error_match = patterns["errors"].search(line)
        if error_match is not None:
            counts["tests_failed"] += int(error_match.group(1))
    counts["tests_total"] = counts["tests_passed"] + counts["tests_failed"]
    return counts


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _safe_metric_slug(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_").lower()
    return re.sub(r"_+", "_", slug) or "unknown"


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _canonical_hash(stream: list[int]) -> str:
    payload = json.dumps(stream, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _usage_snapshot() -> tuple[float, float]:
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (
        float(self_usage.ru_utime + self_usage.ru_stime),
        float(child_usage.ru_utime + child_usage.ru_stime),
    )


def _run_canonical_once() -> dict[str, Any]:
    from zpe_multimodal import IMCDecoder
    from zpe_multimodal.canonical_demo import build_canonical_demo_stream, runtime_voice_capability_mode
    from zpe_multimodal.core.imc import get_kernel_backend_info

    started_at = time.time()
    cpu_self_before, cpu_child_before = _usage_snapshot()
    encode_started_at = time.time()
    stream = build_canonical_demo_stream(require_env=False)
    encode_elapsed = max(1e-9, time.time() - encode_started_at)
    decode_started_at = time.time()
    result = IMCDecoder().decode(stream)
    decode_elapsed = max(1e-9, time.time() - decode_started_at)
    elapsed = max(1e-9, time.time() - started_at)
    cpu_self_after, cpu_child_after = _usage_snapshot()
    cpu_time = (cpu_self_after - cpu_self_before) + (cpu_child_after - cpu_child_before)
    modality_keys = ("text", "diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste")
    coverage_count = sum(1 for key in modality_keys if result.modality_counts.get(key, 0) > 0)
    stream_word_count = len(stream)
    kernel_info = get_kernel_backend_info()
    rust_crate_path = str(CODE_ROOT / "rust" / "imc_kernel")

    return {
        "stream_word_count": stream_word_count,
        "total_stream_word_count": stream_word_count,
        "canonical_run_count": 1,
        "stream_hash": _canonical_hash(stream),
        "stream_valid": bool(result.stream_valid),
        "validation_errors": list(result.validation_errors),
        "modality_counts": dict(result.modality_counts),
        "modality_coverage_count": coverage_count,
        "modality_coverage_all": 1 if coverage_count == len(modality_keys) else 0,
        "voice_capability_mode": runtime_voice_capability_mode(),
        "cpu_core_multiplier": round(cpu_time / elapsed, 4),
        "encode_elapsed_sec": round(encode_elapsed, 4),
        "decode_elapsed_sec": round(decode_elapsed, 4),
        "encode_elapsed_sec_mean": round(encode_elapsed, 4),
        "decode_elapsed_sec_mean": round(decode_elapsed, 4),
        "canonical_elapsed_sec": round(elapsed, 4),
        "elapsed_sec": round(elapsed, 4),
        "canonical_total_words_per_sec": round(_safe_ratio(stream_word_count, elapsed), 4),
        "throughput_encode_words_per_sec": round(stream_word_count / encode_elapsed, 4),
        "throughput_decode_words_per_sec": round(stream_word_count / decode_elapsed, 4),
        "text_length": len(result.text),
        "touch_block_count": len(result.touch_blocks),
        "smell_block_count": len(result.smell_blocks),
        "taste_block_count": len(result.taste_blocks),
        "kernel_backend": str(kernel_info.get("backend", "unknown")),
        "kernel_backend_origin": str(kernel_info.get("origin", "unknown")),
        "kernel_backend_native": 1 if kernel_info.get("native") else 0,
        "kernel_backend_compiled_extension": 1 if kernel_info.get("compiled_extension") else 0,
        "kernel_backend_fallback_used": 1 if kernel_info.get("fallback_used") else 0,
        "kernel_backend_payload_layout": str(kernel_info.get("payload_layout", "")),
        "kernel_backend_ffi_contract_version": str(kernel_info.get("ffi_contract_version", "")),
        "kernel_backend_build_profile": str(kernel_info.get("build_profile", "")),
        "kernel_backend_module_name": str(kernel_info.get("module_name", "")),
        "kernel_backend_module_file": str(kernel_info.get("module_file", "")),
        "kernel_backend_module_suffix": str(kernel_info.get("module_suffix", "")),
        "kernel_backend_module_version": str(kernel_info.get("module_version", "")),
        "kernel_backend_normal_word_count": int(kernel_info.get("normal_word_count", 0)),
        "rust_crate_path": rust_crate_path,
        "rust_extension_module": str(kernel_info.get("module_name", "")),
        "measurement_mode": CANONICAL_PREPASS_MEASUREMENT_MODE,
        "measurement_scope": "single_stream_prepass",
        "authority_run_of_record": 0,
    }


def _canonical_parallel_iterations(stream_word_count: int, worker_count: int) -> int:
    per_round_words = max(1, stream_word_count * max(1, worker_count))
    return max(1, math.ceil(CANONICAL_PARALLEL_MIN_TOTAL_WORDS / per_round_words))


def _parallel_canonical_worker(iterations: int) -> dict[str, Any]:
    from zpe_multimodal import IMCDecoder
    from zpe_multimodal.canonical_demo import build_canonical_demo_stream, runtime_voice_capability_mode
    from zpe_multimodal.core.imc import get_kernel_backend_info

    decoder = IMCDecoder()
    kernel_info = get_kernel_backend_info()
    rust_crate_path = str(CODE_ROOT / "rust" / "imc_kernel")
    modality_keys = ("text", "diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste")

    total_stream_word_count = 0
    total_encode_elapsed = 0.0
    total_decode_elapsed = 0.0
    first_stream_hash = ""
    first_result: dict[str, Any] | None = None

    for _ in range(max(1, iterations)):
        encode_started_at = time.perf_counter()
        stream = build_canonical_demo_stream(require_env=False)
        encode_elapsed = max(1e-9, time.perf_counter() - encode_started_at)

        decode_started_at = time.perf_counter()
        result = decoder.decode(stream)
        decode_elapsed = max(1e-9, time.perf_counter() - decode_started_at)

        stream_word_count = len(stream)
        total_stream_word_count += stream_word_count
        total_encode_elapsed += encode_elapsed
        total_decode_elapsed += decode_elapsed

        if first_result is None:
            coverage_count = sum(1 for key in modality_keys if result.modality_counts.get(key, 0) > 0)
            first_stream_hash = _canonical_hash(stream)
            first_result = {
                "stream_word_count": stream_word_count,
                "stream_hash": first_stream_hash,
                "stream_valid": bool(result.stream_valid),
                "validation_errors": list(result.validation_errors),
                "modality_counts": dict(result.modality_counts),
                "modality_coverage_count": coverage_count,
                "modality_coverage_all": 1 if coverage_count == len(modality_keys) else 0,
                "voice_capability_mode": runtime_voice_capability_mode(),
                "text_length": len(result.text),
                "touch_block_count": len(result.touch_blocks),
                "smell_block_count": len(result.smell_blocks),
                "taste_block_count": len(result.taste_blocks),
                "kernel_backend": str(kernel_info.get("backend", "unknown")),
                "kernel_backend_origin": str(kernel_info.get("origin", "unknown")),
                "kernel_backend_native": 1 if kernel_info.get("native") else 0,
                "kernel_backend_compiled_extension": 1 if kernel_info.get("compiled_extension") else 0,
                "kernel_backend_fallback_used": 1 if kernel_info.get("fallback_used") else 0,
                "kernel_backend_payload_layout": str(kernel_info.get("payload_layout", "")),
                "kernel_backend_ffi_contract_version": str(kernel_info.get("ffi_contract_version", "")),
                "kernel_backend_build_profile": str(kernel_info.get("build_profile", "")),
                "kernel_backend_module_name": str(kernel_info.get("module_name", "")),
                "kernel_backend_module_file": str(kernel_info.get("module_file", "")),
                "kernel_backend_module_suffix": str(kernel_info.get("module_suffix", "")),
                "kernel_backend_module_version": str(kernel_info.get("module_version", "")),
                "kernel_backend_normal_word_count": int(kernel_info.get("normal_word_count", 0)),
                "rust_crate_path": rust_crate_path,
                "rust_extension_module": str(kernel_info.get("module_name", "")),
            }

    if first_result is None:
        return _run_canonical_once()

    first_result["canonical_run_count"] = max(1, iterations)
    first_result["total_stream_word_count"] = total_stream_word_count
    first_result["encode_elapsed_sec"] = round(total_encode_elapsed, 4)
    first_result["decode_elapsed_sec"] = round(total_decode_elapsed, 4)
    first_result["encode_elapsed_sec_mean"] = round(total_encode_elapsed / max(1, iterations), 4)
    first_result["decode_elapsed_sec_mean"] = round(total_decode_elapsed / max(1, iterations), 4)
    first_result["throughput_encode_words_per_sec"] = round(_safe_ratio(total_stream_word_count, total_encode_elapsed), 4)
    first_result["throughput_decode_words_per_sec"] = round(_safe_ratio(total_stream_word_count, total_decode_elapsed), 4)
    return first_result


def _run_parallel_canonical_batch(worker_count: int, batch_iterations: int) -> dict[str, Any]:
    started_at = time.time()
    cpu_self_before, cpu_child_before = _usage_snapshot()
    with ProcessPoolExecutor(max_workers=worker_count) as pool:
        results = list(pool.map(_parallel_canonical_worker, [batch_iterations] * worker_count))
    elapsed = max(1e-9, time.time() - started_at)
    cpu_self_after, cpu_child_after = _usage_snapshot()
    cpu_time = (cpu_self_after - cpu_self_before) + (cpu_child_after - cpu_child_before)

    hashes = {result["stream_hash"] for result in results}
    base = dict(results[0])
    total_stream_word_count = sum(int(result["total_stream_word_count"]) for result in results)
    encode_throughputs = [float(result["throughput_encode_words_per_sec"]) for result in results]
    decode_throughputs = [float(result["throughput_decode_words_per_sec"]) for result in results]
    encode_elapsed_values = [float(result["encode_elapsed_sec"]) for result in results]
    decode_elapsed_values = [float(result["decode_elapsed_sec"]) for result in results]
    base["cpu_core_multiplier"] = round(cpu_time / elapsed, 4)
    base["canonical_elapsed_sec"] = round(elapsed, 4)
    base["elapsed_sec"] = round(elapsed, 4)
    base["parallel_workers"] = worker_count
    base["parallel_hash_consistent"] = 1 if len(hashes) == 1 else 0
    base["parallel_batch_iterations"] = batch_iterations
    base["single_core_prepass_reported"] = 1
    base["measurement_mode"] = CANONICAL_STEADY_STATE_MEASUREMENT_MODE
    base["measurement_scope"] = "saturated_run_of_record"
    base["authority_run_of_record"] = 1
    base["canonical_run_count"] = sum(int(result["canonical_run_count"]) for result in results)
    base["total_stream_word_count"] = total_stream_word_count
    base["canonical_total_words_per_sec"] = round(_safe_ratio(total_stream_word_count, elapsed), 4)
    base["encode_elapsed_sec_mean"] = round(_mean(encode_elapsed_values), 4)
    base["decode_elapsed_sec_mean"] = round(_mean(decode_elapsed_values), 4)
    base["throughput_encode_words_per_sec"] = round(_mean(encode_throughputs), 4)
    base["throughput_decode_words_per_sec"] = round(_mean(decode_throughputs), 4)
    return base


def _rerun_canonical_with_parallel_saturation(worker_count: int, prepass_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    warm_summary = prepass_summary or _run_canonical_once()
    batch_iterations = _canonical_parallel_iterations(int(warm_summary["stream_word_count"]), worker_count)
    target_cpu_multiplier = worker_count * 0.8
    best_summary = _run_parallel_canonical_batch(worker_count, batch_iterations)

    while (
        worker_count > 1
        and float(best_summary["cpu_core_multiplier"]) < target_cpu_multiplier
        and batch_iterations < CANONICAL_PARALLEL_MAX_BATCH_ITERATIONS
    ):
        batch_iterations = min(batch_iterations * 2, CANONICAL_PARALLEL_MAX_BATCH_ITERATIONS)
        best_summary = _run_parallel_canonical_batch(worker_count, batch_iterations)

    best_summary["single_core_prepass_measurement_mode"] = str(
        warm_summary.get("measurement_mode", CANONICAL_PREPASS_MEASUREMENT_MODE)
    )
    best_summary["single_core_prepass_measurement_scope"] = str(warm_summary.get("measurement_scope", "single_stream_prepass"))
    best_summary["single_core_prepass_elapsed_sec"] = float(warm_summary["canonical_elapsed_sec"])
    best_summary["single_core_prepass_total_words_per_sec"] = float(warm_summary["canonical_total_words_per_sec"])
    best_summary["single_core_prepass_encode_words_per_sec"] = float(warm_summary["throughput_encode_words_per_sec"])
    best_summary["single_core_prepass_decode_words_per_sec"] = float(warm_summary["throughput_decode_words_per_sec"])
    best_summary["single_core_prepass_stream_hash"] = str(warm_summary["stream_hash"])
    return best_summary


def _run_canonical_with_cpu_gate(trace: Any | None) -> CanonicalRunResult:
    prepare_span = trace.span(name="prepare_inputs", metadata={"phase": "canonical"}) if trace is not None else None
    if prepare_span is not None:
        prepare_span.end(output={"status": "ok"})

    encode_span = trace.span(name="encode_stream", metadata={"phase": "canonical"}) if trace is not None else None
    summary = _run_canonical_once()
    if encode_span is not None:
        encode_span.end(
            output={
                "stream_word_count": summary["stream_word_count"],
                "stream_hash": summary["stream_hash"],
                "encode_elapsed_sec": summary["encode_elapsed_sec"],
                "throughput_encode_words_per_sec": summary["throughput_encode_words_per_sec"],
            }
        )

    decode_span = trace.span(name="decode_stream", metadata={"phase": "canonical"}) if trace is not None else None
    if decode_span is not None:
        decode_span.end(
            output={
                "stream_valid": summary["stream_valid"],
                "modality_coverage_all": summary["modality_coverage_all"],
                "voice_capability_mode": summary["voice_capability_mode"],
                "decode_elapsed_sec": summary["decode_elapsed_sec"],
                "canonical_total_words_per_sec": summary["canonical_total_words_per_sec"],
                "throughput_decode_words_per_sec": summary["throughput_decode_words_per_sec"],
                "canonical_elapsed_sec": summary["canonical_elapsed_sec"],
            }
        )

    if trace is not None:
        lane_specs = (
            ("lane_text_emoji", {"text_words": summary["modality_counts"]["text"], "bpe_words": summary["modality_counts"]["bpe"]}),
            ("lane_diagram", {"words": summary["modality_counts"]["diagram"]}),
            ("lane_image", {"words": summary["modality_counts"]["image"]}),
            ("lane_music", {"words": summary["modality_counts"]["music"]}),
            ("lane_voice", {"words": summary["modality_counts"]["voice"], "mode": summary["voice_capability_mode"]}),
            ("lane_mental", {"words": summary["modality_counts"]["mental"]}),
            ("lane_touch", {"words": summary["modality_counts"]["touch"], "blocks": summary["touch_block_count"]}),
            ("lane_smell", {"words": summary["modality_counts"]["smell"], "blocks": summary["smell_block_count"]}),
            ("lane_taste", {"words": summary["modality_counts"]["taste"], "blocks": summary["taste_block_count"]}),
        )
        for span_name, payload in lane_specs:
            lane_span = trace.span(name=span_name, metadata={"phase": "canonical"})
            lane_span.end(output=payload)

    cpu_count = max(1, int(os.cpu_count() or 1))
    if summary["cpu_core_multiplier"] >= cpu_count * 0.8:
        return CanonicalRunResult(summary=summary, reran_for_cpu_saturation=False, rerun_workers=1)

    rerun_span = trace.span(name="canonical_rerun_parallel", metadata={"phase": "canonical", "workers": cpu_count}) if trace is not None else None
    rerun_summary = _rerun_canonical_with_parallel_saturation(cpu_count, prepass_summary=summary)
    if rerun_span is not None:
        rerun_span.end(
            output={
                "cpu_core_multiplier": rerun_summary["cpu_core_multiplier"],
                "parallel_hash_consistent": rerun_summary["parallel_hash_consistent"],
                "parallel_workers": rerun_summary["parallel_workers"],
                "canonical_elapsed_sec": rerun_summary["canonical_elapsed_sec"],
                "canonical_total_words_per_sec": rerun_summary["canonical_total_words_per_sec"],
                "throughput_encode_words_per_sec": rerun_summary["throughput_encode_words_per_sec"],
                "throughput_decode_words_per_sec": rerun_summary["throughput_decode_words_per_sec"],
                "total_stream_word_count": rerun_summary["total_stream_word_count"],
            }
        )
    return CanonicalRunResult(summary=rerun_summary, reran_for_cpu_saturation=True, rerun_workers=cpu_count)


def _determinism_hash_match() -> tuple[int, str, str, str]:
    payload = run_probe(runs=2)
    hashes = list(payload.get("hashes", []))
    hash_a = hashes[0] if hashes else ""
    hash_b = hashes[1] if len(hashes) > 1 else hash_a
    probe_id = str(payload.get("probe_id", PROBE_ID))
    return (1 if payload.get("stable") else 0), hash_a, hash_b, probe_id


def _collect_benchmark_summary(output_dir: Path) -> dict[str, Any]:
    artifact_paths = {
        "benchmark_report_path": str(BENCHMARK_REPORT_PATH),
        "hotspot_profile_path": str(HOTSPOT_PROFILE_PATH),
        "benchmark_metrics_dir": str(output_dir),
        "telemetry_log_path": str(BENCHMARK_TELEMETRY),
    }
    if not output_dir.exists():
        return {
            "benchmark_metric_files": 0,
            "benchmark_all_deterministic": 0,
            "benchmark_scenario_count": 0,
            "benchmark_run_id": "",
            "benchmark_git_commit": "",
            "scenario_rows": [],
            "scenario_metrics": {},
            "metric_names": [],
            "metric_file_paths": [],
            "artifact_paths": artifact_paths,
        }
    metrics: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []
    scenario_metrics: dict[str, float] = {}
    metric_names: set[str] = set()
    metric_file_paths: list[str] = []
    run_ids: set[str] = set()
    git_commits: set[str] = set()
    for path in sorted(output_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        metrics.append(payload)
        metric_file_paths.append(str(path))
        scenario = str(payload.get("scenario") or path.stem)
        scenario_slug = _safe_metric_slug(scenario)
        if payload.get("run_id") not in (None, ""):
            run_ids.add(str(payload["run_id"]))
        if payload.get("git_commit") not in (None, ""):
            git_commits.add(str(payload["git_commit"]))

        row = {
            "scenario": scenario,
            "metric_file_path": str(path),
            "dataset_or_fixture": str(payload.get("dataset_or_fixture", "")),
            "run_id": str(payload.get("run_id", "")),
            "git_commit": str(payload.get("git_commit", "")),
            "deterministic": 1 if payload.get("deterministic") else 0,
        }
        for key in BENCHMARK_SCALAR_KEYS:
            value = payload.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                numeric_value = round(float(value), 4)
                row[key] = numeric_value
                metric_name = f"benchmark__{scenario_slug}__{key}"
                scenario_metrics[metric_name] = numeric_value
                metric_names.add(metric_name)
        scenario_rows.append(row)
    deterministic = all(bool(item.get("deterministic")) for item in metrics) if metrics else False
    return {
        "benchmark_metric_files": len(metrics),
        "benchmark_all_deterministic": 1 if deterministic else 0,
        "benchmark_scenario_count": len(scenario_rows),
        "benchmark_run_id": sorted(run_ids)[0] if len(run_ids) == 1 else "",
        "benchmark_git_commit": sorted(git_commits)[0] if len(git_commits) == 1 else "",
        "scenario_rows": scenario_rows,
        "scenario_metrics": scenario_metrics,
        "metric_names": sorted(metric_names),
        "metric_file_paths": metric_file_paths,
        "artifact_paths": artifact_paths,
    }


def _round_metric(value: float, *, digits: int = 6) -> float:
    return round(float(value), digits)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _mean_available(values: list[float | None]) -> float:
    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def _metric_summary_map(summary_rows: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in summary_rows:
        name = str(row.get("name") or row.get("metricName") or "")
        if not name:
            continue
        current = row.get("valueCurrent")
        if current is None:
            current = row.get("metricValueCurrent")
        if current is None:
            current = row.get("lastValue")
        if current is None:
            current = row.get("valueMax")
        if current is None:
            continue
        try:
            out[name] = float(current)
        except Exception:
            continue
    return out


def _summary_float(summary: Mapping[str, float], *keys: str) -> float | None:
    for key in keys:
        if key in summary:
            return float(summary[key])
    return None


def _curated_final_specs() -> list[tuple[str, str]]:
    specs = [
        ("truth/tests_pass_rate", "tests_pass_rate"),
        ("truth/determinism_match", "determinism_match"),
        ("truth/imc_score", "imc_score"),
        ("truth/transport_score", "transport_score"),
        ("truth/tests_passed", "tests_passed"),
        ("truth/tests_total", "tests_total"),
        ("performance/words_per_sec", "words_per_sec"),
        ("performance/run_duration_sec", "run_duration_sec"),
        ("performance/gzip_ratio", "gzip_ratio"),
        ("performance/stream_word_count", "stream_word_count"),
        ("distribution/entropy_bits", "entropy_bits"),
        ("distribution/hhi_concentration", "hhi_concentration"),
        ("distribution/max_share", "max_share"),
        ("distribution/min_nonzero_share", "min_nonzero_share"),
        ("distribution/effective_modality_count", "effective_modality_count"),
        ("distribution/horizontal_breadth", "horizontal_breadth"),
        ("distribution/vertical_dominance", "vertical_dominance"),
        ("distribution/top2_pair_share", "top2_pair_share"),
        ("distribution/top2_pair_balance", "top2_pair_balance"),
        ("distribution/bimodality_index", "bimodality_index"),
        ("distribution/top1_top2_gap", "top1_top2_gap"),
        ("transport/coverage", "transport_coverage"),
        ("transport/safety", "transport_safety"),
        ("transport/reserved_mode_norm", "transport_reserved_mode_norm"),
        ("transport/entropy", "transport_entropy"),
        ("transport/hhi", "transport_hhi"),
        ("transport/max_share", "transport_max_share"),
        ("transport/throughput", "transport_throughput"),
    ]
    specs.extend((f"modality_share/{modality}", f"share_{modality}") for modality in CANONICAL_MODALITIES)
    specs.extend((f"mode_share/{mode}", f"mode_share_{mode}") for mode in MODE_ORDER)
    return specs


def _curated_inrun_specs() -> list[tuple[str, str]]:
    specs = [
        ("run/progress_fraction", "progress_fraction"),
        ("run/checkpoint_word", "checkpoint_word"),
        ("run/word_index", "word_index"),
        ("run/transition_density", "transition_density"),
        ("run/avg_segment_length", "avg_segment_length"),
        ("distribution/coverage_count", "coverage_count"),
        ("distribution/effective_modality_count", "effective_modality_count"),
        ("distribution/entropy_bits", "entropy_bits"),
        ("distribution/hhi_concentration", "hhi_concentration"),
        ("distribution/max_share", "max_share"),
        ("distribution/min_nonzero_share", "min_nonzero_share"),
        ("distribution/top1_top2_gap", "top1_top2_gap"),
        ("distribution/top2_pair_balance", "top2_pair_balance"),
        ("distribution/top2_pair_share", "top2_pair_share"),
        ("distribution/bimodality_index", "bimodality_index"),
        ("transport/coverage", "transport_coverage"),
        ("transport/safety", "transport_safety"),
        ("transport/reserved_mode_norm", "transport_reserved_mode_norm"),
        ("transport/entropy_norm", "transport_entropy"),
        ("transport/hhi_norm", "transport_hhi"),
        ("transport/max_share_norm", "transport_max_share"),
        ("transport/score_proxy", "transport_score_proxy"),
    ]
    specs.extend((f"modality_share/{modality}", f"share_{modality}") for modality in CANONICAL_MODALITIES)
    specs.extend((f"mode_share/{mode}", f"mode_share_{mode}") for mode in MODE_ORDER)
    return specs


def _distribution_metrics_from_shares(shares: Mapping[str, float]) -> dict[str, float]:
    values = [float(shares[modality]) for modality in CANONICAL_MODALITIES if float(shares.get(modality, 0.0)) > 0.0]
    entropy_bits = 0.0
    if values:
        entropy_bits = -sum(value * math.log2(value) for value in values)
    hhi = sum(value * value for value in values)
    max_share = max(values) if values else 0.0
    min_nonzero_share = min(values) if values else 0.0
    sorted_values = sorted(values, reverse=True)
    top1 = sorted_values[0] if len(sorted_values) >= 1 else 0.0
    top2 = sorted_values[1] if len(sorted_values) >= 2 else 0.0
    pair_share = top1 + top2
    pair_balance = 1.0 - abs(top1 - top2) / pair_share if pair_share > 0 else 0.0
    coverage_count = len(values)
    effective_modality_count = 1.0 / hhi if hhi > 0 else 0.0
    horizontal_breadth = entropy_bits / math.log2(coverage_count) if coverage_count > 1 else 0.0
    return {
        "coverage_count": float(coverage_count),
        "entropy_bits": entropy_bits,
        "hhi_concentration": hhi,
        "max_share": max_share,
        "min_nonzero_share": min_nonzero_share,
        "effective_modality_count": effective_modality_count,
        "horizontal_breadth": horizontal_breadth,
        "vertical_dominance": max_share,
        "top2_pair_share": pair_share,
        "top2_pair_balance": pair_balance,
        "bimodality_index": pair_share * pair_balance,
        "top1_top2_gap": top1 - top2,
    }


def _transport_metrics(
    *,
    distribution: Mapping[str, float],
    mode_reserved_share: float | None,
    reserved_non_mental_count: float | None,
    throughput_words_per_sec: float | None,
) -> dict[str, float]:
    coverage = _safe_ratio(float(distribution.get("coverage_count", 0.0)), float(len(CANONICAL_MODALITIES)))
    safety = 1.0 if float(reserved_non_mental_count or 0.0) <= 0.0 else 0.0
    reserved_share = float(mode_reserved_share or 0.0)
    reserved_norm = _clamp01(1.0 - min(reserved_share / TRANSPORT_RESERVED_SHARE_THRESHOLD, 1.0))
    entropy_norm = _safe_ratio(float(distribution.get("entropy_bits", 0.0)), math.log2(len(CANONICAL_MODALITIES)))
    hhi_norm = 1.0 - float(distribution.get("hhi_concentration", 0.0))
    max_share_norm = 1.0 - float(distribution.get("max_share", 0.0))
    throughput_norm = None
    if throughput_words_per_sec is not None:
        throughput_norm = _clamp01(float(throughput_words_per_sec) / TRANSPORT_THROUGHPUT_TARGET_WPS)

    score_proxy = _mean_available([coverage, safety, reserved_norm, entropy_norm, hhi_norm, max_share_norm])
    transport_score = 100.0 * _mean_available(
        [coverage, safety, reserved_norm, entropy_norm, hhi_norm, max_share_norm, throughput_norm]
    )
    return {
        "transport_coverage": coverage,
        "transport_safety": safety,
        "transport_reserved_mode_norm": reserved_norm,
        "transport_entropy": entropy_norm,
        "transport_hhi": hhi_norm,
        "transport_max_share": max_share_norm,
        "transport_throughput": float(throughput_norm or 0.0),
        "transport_score_proxy": score_proxy,
        "transport_score": transport_score,
    }


def _history_share_map(summary: Mapping[str, float], total_words: float) -> dict[str, float]:
    shares: dict[str, float] = {}
    for modality in CANONICAL_MODALITIES:
        value = _summary_float(
            summary,
            f"{CURATED_METRIC_PREFIX}/modality_share/{modality}/final",
            f"share_{modality}",
        )
        if value is None:
            count_value = _summary_float(summary, f"count_{modality}")
            if count_value is not None and total_words > 0:
                value = _safe_ratio(count_value, total_words)
        shares[modality] = float(value or 0.0)
    return shares


def _history_mode_share(summary: Mapping[str, float], mode: str, total_words: float) -> float | None:
    value = _summary_float(
        summary,
        f"{CURATED_METRIC_PREFIX}/mode_share/{mode}/final",
        f"mode_{mode}_share",
    )
    if value is not None:
        return float(value)
    count_value = _summary_float(summary, f"mode_{mode}_count")
    if count_value is not None and total_words > 0:
        return _safe_ratio(count_value, total_words)
    return None


def _history_total_words(summary: Mapping[str, float]) -> float:
    total_words = _summary_float(
        summary,
        f"{CURATED_METRIC_PREFIX}/performance/stream_word_count/final",
        "stream_word_count_smoke",
    )
    if total_words is not None:
        return float(total_words)
    count_total = sum(float(_summary_float(summary, f"count_{modality}") or 0.0) for modality in CANONICAL_MODALITIES)
    return float(count_total)


def _history_feature_row(summary: Mapping[str, float], *, run_timestamp_ms: int, name: str) -> dict[str, float] | None:
    lower_name = name.lower()
    if any(token in lower_name for token in ("curated layout", "visual pack", "end-to-end modality run |")):
        return None

    tests_total = _summary_float(summary, f"{CURATED_METRIC_PREFIX}/truth/tests_total/final", "tests_total")
    stream_word_count = _history_total_words(summary)
    if tests_total is None or tests_total <= 0 or stream_word_count <= 0:
        return None

    tests_passed = _summary_float(summary, f"{CURATED_METRIC_PREFIX}/truth/tests_passed/final", "tests_passed") or 0.0
    tests_pass_rate = _summary_float(summary, f"{CURATED_METRIC_PREFIX}/truth/tests_pass_rate/final")
    if tests_pass_rate is None:
        tests_pass_rate = _safe_ratio(tests_passed, tests_total)

    determinism_match = _summary_float(
        summary,
        f"{CURATED_METRIC_PREFIX}/truth/determinism_match/final",
        "determinism_hash_match",
    ) or 0.0
    words_per_sec = _summary_float(
        summary,
        f"{CURATED_METRIC_PREFIX}/performance/words_per_sec/final",
        "canonical_total_words_per_sec",
        "throughput_encode_words_per_sec",
        "words_per_sec",
    )
    run_duration_sec = _summary_float(
        summary,
        f"{CURATED_METRIC_PREFIX}/performance/run_duration_sec/final",
        "canonical_elapsed_sec",
        "run_duration_sec",
    ) or 0.0
    gzip_ratio = _summary_float(summary, f"{CURATED_METRIC_PREFIX}/performance/gzip_ratio/final", "gzip_ratio") or 0.0
    shares = _history_share_map(summary, stream_word_count)
    distribution = _distribution_metrics_from_shares(shares)
    mode_reserved_share = _history_mode_share(summary, "reserved", stream_word_count)
    reserved_non_mental_count = _summary_float(summary, "reserved_non_mental_count")
    transport = _transport_metrics(
        distribution=distribution,
        mode_reserved_share=mode_reserved_share,
        reserved_non_mental_count=reserved_non_mental_count,
        throughput_words_per_sec=words_per_sec,
    )
    transport_score = _summary_float(
        summary,
        f"{CURATED_METRIC_PREFIX}/truth/transport_score/final",
        "truth/transport_score",
    )
    if transport_score is None:
        transport_score = transport["transport_score"]

    transport_safety = _summary_float(summary, f"{CURATED_METRIC_PREFIX}/transport/safety/final", "transport/safety")
    if transport_safety is None:
        transport_safety = transport["transport_safety"]
    transport_coverage = _summary_float(summary, f"{CURATED_METRIC_PREFIX}/transport/coverage/final", "transport/coverage")
    if transport_coverage is None:
        transport_coverage = transport["transport_coverage"]

    imc_score = _summary_float(summary, f"{CURATED_METRIC_PREFIX}/truth/imc_score/final", "truth/imc_score")
    if imc_score is None:
        imc_score = 100.0 * _mean_available([tests_pass_rate, determinism_match, transport_coverage, transport_safety])

    feature_row: dict[str, float] = {
        "run_timestamp_ms": float(run_timestamp_ms),
        "tests_total": float(tests_total),
        "tests_passed": float(tests_passed),
        "tests_pass_rate": float(tests_pass_rate),
        "determinism_match": float(determinism_match),
        "imc_score": float(imc_score),
        "transport_score": float(transport_score),
        "words_per_sec": float(words_per_sec or 0.0),
        "run_duration_sec": float(run_duration_sec),
        "gzip_ratio": float(gzip_ratio),
        "stream_word_count": float(stream_word_count),
        **distribution,
        **transport,
    }
    for modality, share in shares.items():
        feature_row[f"share_{modality}"] = float(share)
    for mode in MODE_ORDER:
        mode_share = _history_mode_share(summary, mode, stream_word_count)
        if mode_share is not None:
            feature_row[f"mode_share_{mode}"] = float(mode_share)
    return feature_row


def _checkpoint_indices(total_words: int, *, point_count: int = CURATED_INRUN_CHECKPOINTS) -> list[int]:
    if total_words <= 0:
        return []
    checkpoints = sorted(
        {
            max(1, min(total_words, int(round(total_words * step / max(1, point_count)))))
            for step in range(1, point_count + 1)
        }
    )
    if checkpoints[-1] != total_words:
        checkpoints.append(total_words)
    return checkpoints


def _canonical_feature_row(
    *,
    pytest_counts: dict[str, int],
    canonical_result: CanonicalRunResult,
) -> tuple[dict[str, float], list[dict[str, float]]]:
    from zpe_multimodal.canonical_demo import build_canonical_demo_stream
    from zpe_multimodal.core.constants import Mode
    from zpe_multimodal.core.imc import iter_stream
    from zpe_multimodal.mental.pack import MENTAL_TYPE_BIT

    stream = build_canonical_demo_stream(require_env=False)
    stream_hash = _canonical_hash(stream)
    if stream_hash != canonical_result.summary["stream_hash"]:
        raise RuntimeError("canonical stream hash drift during panel metric derivation")

    modality_sequence = [modality for modality, _ in iter_stream(stream)]
    raw_word_bytes = bytearray()
    mode_sequence: list[str] = []
    reserved_non_mental_total = 0
    mode_counts = {mode: 0 for mode in MODE_ORDER}
    for word in stream:
        raw_word_bytes.extend(int(word).to_bytes(4, "big", signed=False))
        mode_value = (int(word) >> 18) & 0x3
        if mode_value == Mode.NORMAL.value:
            mode_name = "normal"
        elif mode_value == Mode.ESCAPE.value:
            mode_name = "escape"
        elif mode_value == Mode.EXTENSION.value:
            mode_name = "extension"
        else:
            mode_name = "reserved"
            payload = int(word) & 0xFFFF
            if (payload & MENTAL_TYPE_BIT) == 0:
                reserved_non_mental_total += 1
        mode_counts[mode_name] += 1
        mode_sequence.append(mode_name)

    total_words = len(modality_sequence)
    if total_words != len(stream) or len(mode_sequence) != total_words:
        raise RuntimeError("canonical stream modality analysis did not preserve word cardinality")

    modality_counts = {modality: int(canonical_result.summary["modality_counts"].get(modality, 0)) for modality in CANONICAL_MODALITIES}
    shares = {modality: _safe_ratio(count, total_words) for modality, count in modality_counts.items()}
    distribution = _distribution_metrics_from_shares(shares)
    mode_shares = {mode: _safe_ratio(count, total_words) for mode, count in mode_counts.items()}
    transport = _transport_metrics(
        distribution=distribution,
        mode_reserved_share=mode_shares["reserved"],
        reserved_non_mental_count=float(reserved_non_mental_total),
        throughput_words_per_sec=float(
            canonical_result.summary.get(
                "canonical_total_words_per_sec",
                canonical_result.summary["throughput_encode_words_per_sec"],
            )
        ),
    )
    gzip_stream_bytes = len(gzip.compress(bytes(raw_word_bytes)))
    raw_stream_bytes = len(raw_word_bytes)
    current_row: dict[str, float] = {
        "run_timestamp_ms": float(int(time.time() * 1000)),
        "tests_total": float(pytest_counts["tests_total"]),
        "tests_passed": float(pytest_counts["tests_passed"]),
        "tests_pass_rate": _safe_ratio(pytest_counts["tests_passed"], max(1, pytest_counts["tests_total"])),
        "determinism_match": 1.0,
        "words_per_sec": float(
            canonical_result.summary.get(
                "canonical_total_words_per_sec",
                canonical_result.summary["throughput_encode_words_per_sec"],
            )
        ),
        "run_duration_sec": float(canonical_result.summary["canonical_elapsed_sec"]),
        "gzip_ratio": _safe_ratio(gzip_stream_bytes, max(1, raw_stream_bytes)),
        "stream_word_count": float(total_words),
        **distribution,
        **transport,
    }
    current_row["imc_score"] = 100.0 * _mean_available(
        [
            current_row["tests_pass_rate"],
            current_row["determinism_match"],
            transport["transport_coverage"],
            transport["transport_safety"],
        ]
    )
    current_row["transport_score"] = float(transport["transport_score"])
    for modality, share in shares.items():
        current_row[f"share_{modality}"] = float(share)
    for mode, share in mode_shares.items():
        current_row[f"mode_share_{mode}"] = float(share)
    checkpoints = _checkpoint_indices(total_words)
    inrun_rows: list[dict[str, float]] = []
    prefix_counts = {modality: 0 for modality in CANONICAL_MODALITIES}
    prefix_mode_counts = {mode: 0 for mode in MODE_ORDER}
    prefix_reserved_non_mental = 0
    transitions = 0
    cursor = 0
    previous_modality: str | None = None
    for step, checkpoint_word in enumerate(checkpoints, start=1):
        while cursor < checkpoint_word:
            modality = modality_sequence[cursor]
            mode_name = mode_sequence[cursor]
            prefix_counts[modality] += 1
            prefix_mode_counts[mode_name] += 1
            if mode_name == "reserved":
                payload = int(stream[cursor]) & 0xFFFF
                if (payload & MENTAL_TYPE_BIT) == 0:
                    prefix_reserved_non_mental += 1
            if previous_modality is not None and modality != previous_modality:
                transitions += 1
            previous_modality = modality
            cursor += 1

        prefix_total = float(checkpoint_word)
        prefix_shares = {modality: _safe_ratio(count, prefix_total) for modality, count in prefix_counts.items()}
        prefix_distribution = _distribution_metrics_from_shares(prefix_shares)
        prefix_transport = _transport_metrics(
            distribution=prefix_distribution,
            mode_reserved_share=_safe_ratio(prefix_mode_counts["reserved"], prefix_total),
            reserved_non_mental_count=float(prefix_reserved_non_mental),
            throughput_words_per_sec=None,
        )
        segment_count = transitions + 1 if checkpoint_word > 0 else 0
        row: dict[str, float] = {
            "progress_fraction": _safe_ratio(checkpoint_word, total_words),
            "checkpoint_word": float(checkpoint_word),
            "word_index": float(checkpoint_word),
            "transition_density": _safe_ratio(transitions, max(1, checkpoint_word - 1)),
            "avg_segment_length": _safe_ratio(checkpoint_word, max(1, segment_count)),
            **prefix_distribution,
            **prefix_transport,
        }
        for modality, share in prefix_shares.items():
            row[f"share_{modality}"] = float(share)
        for mode in MODE_ORDER:
            row[f"mode_share_{mode}"] = _safe_ratio(prefix_mode_counts[mode], prefix_total)
        inrun_rows.append(row)

    return current_row, inrun_rows


def _curated_final_metrics(feature_row: Mapping[str, float]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for path, feature_key in _curated_final_specs():
        value = feature_row.get(feature_key)
        if isinstance(value, (int, float)):
            metrics[f"{CURATED_METRIC_PREFIX}/{path}/final"] = _round_metric(float(value))
    return metrics


def _curated_cross_run_series(history_rows: list[Mapping[str, float]]) -> dict[str, list[tuple[int, float]]]:
    series: dict[str, list[tuple[int, float]]] = {
        f"{CURATED_METRIC_PREFIX}/run/index/trend": [],
        f"{CURATED_METRIC_PREFIX}/run/timestamp_ms/trend": [],
    }
    for step, row in enumerate(history_rows, start=1):
        series[f"{CURATED_METRIC_PREFIX}/run/index/trend"].append((step, float(step)))
        timestamp_ms = row.get("run_timestamp_ms")
        if isinstance(timestamp_ms, (int, float)):
            series[f"{CURATED_METRIC_PREFIX}/run/timestamp_ms/trend"].append((step, _round_metric(float(timestamp_ms))))

    for path, feature_key in _curated_final_specs():
        metric_name = f"{CURATED_METRIC_PREFIX}/{path}/trend"
        points: list[tuple[int, float]] = []
        for step, row in enumerate(history_rows, start=1):
            value = row.get(feature_key)
            if isinstance(value, (int, float)):
                points.append((step, _round_metric(float(value))))
        if points:
            series[metric_name] = points
    return series


def _curated_inrun_series(inrun_rows: list[Mapping[str, float]]) -> dict[str, list[tuple[int, float]]]:
    series: dict[str, list[tuple[int, float]]] = {}
    for path, feature_key in _curated_inrun_specs():
        metric_name = f"{CURATED_METRIC_PREFIX}/inrun/{path}/trend"
        points: list[tuple[int, float]] = []
        for step, row in enumerate(inrun_rows, start=1):
            value = row.get(feature_key)
            if isinstance(value, (int, float)):
                points.append((step, _round_metric(float(value))))
        if points:
            series[metric_name] = points
    return series


def _curated_benchmark_series(telemetry_path: Path) -> dict[str, list[tuple[int, float]]]:
    if not telemetry_path.exists():
        return {}

    series: dict[str, list[tuple[int, float]]] = {}
    scenario_index = 0
    scenario_count_selected = 0
    for line in telemetry_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if payload.get("event_type") == "run_start":
            scenario_count_selected = int(payload.get("scenario_count_selected") or 0)
        if payload.get("phase") != "scenario_complete":
            continue
        scenario_index += 1
        scenario_slug = _safe_metric_slug(str(payload.get("scenario") or f"scenario_{scenario_index}"))
        if scenario_count_selected > 0:
            series.setdefault(f"{CURATED_METRIC_PREFIX}/benchmark/run/progress_fraction/trend", []).append(
                (scenario_index, _round_metric(_safe_ratio(scenario_index, scenario_count_selected)))
            )
        series.setdefault(f"{CURATED_METRIC_PREFIX}/benchmark/run/scenario_index/trend", []).append(
            (scenario_index, float(scenario_index))
        )
        for key in BENCHMARK_SCALAR_KEYS:
            value = payload.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                metric_name = f"{CURATED_METRIC_PREFIX}/benchmark/{scenario_slug}/{key}/trend"
                series.setdefault(metric_name, []).append((scenario_index, _round_metric(float(value), digits=4)))
    return series


def _load_curated_history(workspace: str, project_name: str, current_row: Mapping[str, float]) -> list[dict[str, float]]:
    history_rows: list[dict[str, float]] = []
    try:
        from comet_ml.api import API  # type: ignore
    except Exception:
        return [dict(current_row)]

    try:
        api = API(api_key=os.environ.get("COMET_API_KEY") or None)
        experiments = api.get_experiments(workspace, project_name)
    except Exception:
        return [dict(current_row)]

    candidates: list[tuple[int, Any]] = []
    for experiment in experiments:
        timestamp_ms = int(
            getattr(experiment, "end_server_timestamp", None)
            or getattr(experiment, "start_server_timestamp", None)
            or 0
        )
        candidates.append((timestamp_ms, experiment))
    candidates.sort(key=lambda item: item[0])

    for timestamp_ms, experiment in candidates[-24:]:
        try:
            summary_map = _metric_summary_map(experiment.get_metrics_summary())
            feature_row = _history_feature_row(
                summary_map,
                run_timestamp_ms=timestamp_ms,
                name=str(getattr(experiment, "name", "") or getattr(experiment, "get_name", lambda: "")()),
            )
        except Exception:
            continue
        if feature_row is not None:
            history_rows.append(feature_row)

    trimmed = history_rows[-max(0, CURATED_HISTORY_LOOKBACK - 1) :]
    trimmed.append(dict(current_row))
    return trimmed


def _build_curated_surface(
    *,
    workspace: str,
    project_name: str,
    pytest_counts: dict[str, int],
    canonical_result: CanonicalRunResult,
    benchmark_telemetry_path: Path,
) -> CuratedMetricSurface:
    current_row, inrun_rows = _canonical_feature_row(pytest_counts=pytest_counts, canonical_result=canonical_result)
    history_rows = _load_curated_history(workspace, project_name, current_row)
    final_metrics = _curated_final_metrics(current_row)
    inrun_series = _curated_inrun_series(inrun_rows)
    cross_run_series = _curated_cross_run_series(history_rows)
    benchmark_series = _curated_benchmark_series(benchmark_telemetry_path)
    metric_names = sorted(set(final_metrics) | set(inrun_series) | set(cross_run_series) | set(benchmark_series))
    parameter_values = {
        "display_metric_layers": "final+trend_history+trend_inrun",
        "display_panel_namespace": CURATED_METRIC_PREFIX,
        "display_trend_mode": "recent_canonical_runs",
        "display_trend_policy": "curated_surface_only",
        "display_inrun_enabled": 1,
        "display_inrun_point_count": len(inrun_rows),
        "display_inrun_metric_count": len(inrun_series),
        "display_cross_run_metric_count": len(cross_run_series),
        "display_benchmark_progress_metric_count": len(benchmark_series),
        "display_blank_slate_reference_run": "403569ea5d79453f8708c16b0d3e994a",
    }
    return CuratedMetricSurface(
        final_metrics=final_metrics,
        inrun_series=inrun_series,
        cross_run_series=cross_run_series,
        benchmark_series=benchmark_series,
        parameter_values=parameter_values,
        metric_names=metric_names,
    )


def _project_identity(payload: Any) -> dict[str, str]:
    candidates: dict[str, str] = {}
    if isinstance(payload, dict):
        source = payload
        for out_key, in_keys in (
            ("name", ("name", "projectName", "project_name")),
            ("id", ("id", "projectId", "project_id")),
            ("slug", ("slug", "projectSlug", "project_slug")),
            ("url", ("url", "projectUrl", "project_url")),
        ):
            for key in in_keys:
                if source.get(key) not in (None, ""):
                    candidates[out_key] = str(source[key])
                    break
        return candidates

    for out_key, attr_name in (("name", "name"), ("id", "id"), ("slug", "slug"), ("url", "url")):
        value = getattr(payload, attr_name, None)
        if value not in (None, ""):
            candidates[out_key] = str(value)
    return candidates


def _verify_classic_comet_project(*, workspace: str, expected_name: str) -> ProjectCheck:
    try:
        from comet_ml.api import API  # type: ignore
    except Exception as exc:
        return ProjectCheck(target="classic_comet", status="HOLD", handshake_error=f"comet_ml unavailable: {exc}")

    try:
        api = API(api_key=os.environ.get("COMET_API_KEY") or None)
        project = api.get_project(workspace, expected_name)
        if project is None:
            api.create_project(workspace, expected_name)
            project = api.get_project(workspace, expected_name)
            if project is None:
                return ProjectCheck(
                    target="classic_comet",
                    status="HOLD",
                    handshake_error=f"project create returned no project for {expected_name}",
                )
            identity = _project_identity(project)
            return ProjectCheck(
                target="classic_comet",
                status="CREATED",
                resolved_name=identity.get("name", expected_name),
                resolved_id=identity.get("id"),
                resolved_slug=identity.get("slug"),
                url=identity.get("url"),
                detail=identity,
            )
        identity = _project_identity(project)
        return ProjectCheck(
            target="classic_comet",
            status="EXISTS",
            resolved_name=identity.get("name", expected_name),
            resolved_id=identity.get("id"),
            resolved_slug=identity.get("slug"),
            url=identity.get("url"),
            detail=identity,
        )
    except Exception as exc:
        return ProjectCheck(
            target="classic_comet",
            status="HOLD",
            handshake_error=f"{type(exc).__name__}: {exc}",
        )


def _verify_opik_project(*, workspace: str, expected_name: str, host: str) -> ProjectCheck:
    try:
        from opik import Opik  # type: ignore
        from opik.rest_api.core.api_error import ApiError  # type: ignore
    except Exception as exc:
        return ProjectCheck(target="opik", status="HOLD", handshake_error=f"opik unavailable: {exc}")

    client = None
    try:
        client = Opik(
            project_name=expected_name,
            workspace=workspace,
            host=host,
            api_key=_opik_api_key() or None,
            _use_batching=True,
            _show_misconfiguration_message=False,
        )
        client.auth_check()
        try:
            project = client.rest_client.projects.retrieve_project(name=expected_name)
            url = client.get_project_url(expected_name)
            return ProjectCheck(
                target="opik",
                status="EXISTS",
                resolved_name=getattr(project, "name", expected_name),
                resolved_id=getattr(project, "id", None),
                url=url,
            )
        except ApiError as exc:
            if getattr(exc, "status_code", None) != 404:
                raise
            client.rest_client.projects.create_project(name=expected_name)
            project = client.rest_client.projects.retrieve_project(name=expected_name)
            url = client.get_project_url(expected_name)
            return ProjectCheck(
                target="opik",
                status="CREATED",
                resolved_name=getattr(project, "name", expected_name),
                resolved_id=getattr(project, "id", None),
                url=url,
            )
    except Exception as exc:
        return ProjectCheck(
            target="opik",
            status="HOLD",
            handshake_error=f"{type(exc).__name__}: {exc}",
        )
    finally:
        if client is not None:
            try:
                client.end()
            except Exception:
                pass


def _write_env_check(
    path: Path,
    *,
    workspace: str,
    classic_check: ProjectCheck,
    opik_check: ProjectCheck,
    classic_remote_enabled: bool,
    opik_remote_enabled: bool,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "IMC DUAL LOGGING ENV CHECK",
        f"WORKSPACE={workspace}",
        "RELEASE_DEFAULT_LOCAL_ONLY=1",
        f"CLASSIC_REMOTE_ENABLED={1 if classic_remote_enabled else 0}",
        f"COMET_API_KEY_PRESENT={1 if os.environ.get('COMET_API_KEY') else 0}",
        f"COMET_WORKSPACE={os.environ.get('COMET_WORKSPACE', '') or '(unset)'}",
        f"COMET_PROJECT_EXPECTED={DEFAULT_CLASSIC_PROJECT}",
        f"COMET_PROJECT_STATUS={classic_check.status}",
        f"COMET_PROJECT_RESOLVED_NAME={classic_check.resolved_name or '(unset)'}",
        f"COMET_PROJECT_RESOLVED_ID={classic_check.resolved_id or '(unset)'}",
        f"COMET_PROJECT_RESOLVED_SLUG={classic_check.resolved_slug or '(unset)'}",
        f"COMET_HANDSHAKE_ERROR={classic_check.handshake_error or '(none)'}",
        f"OPIK_REMOTE_ENABLED={1 if opik_remote_enabled else 0}",
        f"OPIK_API_KEY_PRESENT={1 if os.environ.get('OPIK_API_KEY') else 0}",
        f"OPIK_EFFECTIVE_API_KEY_PRESENT={1 if _opik_api_key() else 0}",
        f"OPIK_API_KEY_SOURCE={_opik_api_key_source()}",
        f"OPIK_WORKSPACE={os.environ.get('OPIK_WORKSPACE', '') or '(unset)'}",
        f"OPIK_URL_OVERRIDE={os.environ.get('OPIK_URL_OVERRIDE', '') or DEFAULT_OPIK_URL}",
        f"OPIK_PROJECT_EXPECTED={DEFAULT_OPIK_PROJECT}",
        f"OPIK_PROJECT_STATUS={opik_check.status}",
        f"OPIK_PROJECT_RESOLVED_NAME={opik_check.resolved_name or '(unset)'}",
        f"OPIK_PROJECT_RESOLVED_ID={opik_check.resolved_id or '(unset)'}",
        f"OPIK_PROJECT_URL={opik_check.url or '(unset)'}",
        f"OPIK_HANDSHAKE_ERROR={opik_check.handshake_error or '(none)'}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _proof_bundle_complete(paths: list[Path]) -> int:
    return 1 if all(path.exists() for path in paths) else 0


def _build_proof_manifest(
    *,
    status: str,
    workspace: str,
    run_name: str,
    classic_check: ProjectCheck,
    opik_check: ProjectCheck,
    comet_identity: dict[str, str],
    opik_trace_id: str,
    opik_trace_url: str,
    benchmark_summary: dict[str, Any],
    canonical_result: CanonicalRunResult,
    pytest_counts: dict[str, int],
    pytest_result: CommandResult,
    sensation_result: CommandResult,
    fidelity_result: CommandResult,
    cross_modal_result: CommandResult,
    benchmark_result: CommandResult,
    det_match: int,
    hash_a: str,
    hash_b: str,
    probe_id: str,
    metric_names: list[str],
    env_check_path: Path,
    run_log_path: Path,
    proof_reference_mode: str,
) -> dict[str, Any]:
    return {
        "generated_at_utc": _utc_now(),
        "status": status,
        "run_kind": "canonical-promotion",
        "run_name": run_name,
        "workspace": workspace,
        "run_of_record": {
            "type": "saturated_canonical",
            "canonical_measurement_mode": str(
                canonical_result.summary.get("measurement_mode", CANONICAL_STEADY_STATE_MEASUREMENT_MODE)
            ),
            "canonical_measurement_scope": str(
                canonical_result.summary.get("measurement_scope", "saturated_run_of_record")
            ),
            "single_core_prepass_reported": bool(canonical_result.summary.get("single_core_prepass_reported", 0)),
            "single_core_prepass_measurement_mode": str(
                canonical_result.summary.get("single_core_prepass_measurement_mode", CANONICAL_PREPASS_MEASUREMENT_MODE)
            ),
            "single_core_prepass_measurement_scope": str(
                canonical_result.summary.get("single_core_prepass_measurement_scope", "single_stream_prepass")
            ),
            "single_core_prepass_elapsed_sec": canonical_result.summary.get("single_core_prepass_elapsed_sec"),
            "single_core_prepass_total_words_per_sec": canonical_result.summary.get(
                "single_core_prepass_total_words_per_sec"
            ),
            "single_core_prepass_encode_words_per_sec": canonical_result.summary.get(
                "single_core_prepass_encode_words_per_sec"
            ),
            "single_core_prepass_decode_words_per_sec": canonical_result.summary.get(
                "single_core_prepass_decode_words_per_sec"
            ),
            "single_core_prepass_stream_hash": canonical_result.summary.get("single_core_prepass_stream_hash", ""),
            "canonical_reran_for_cpu_saturation": canonical_result.reran_for_cpu_saturation,
            "canonical_parallel_workers": canonical_result.rerun_workers,
            "canonical_parallel_batch_iterations": canonical_result.summary.get("parallel_batch_iterations", 1),
            "canonical_cpu_core_multiplier": canonical_result.summary["cpu_core_multiplier"],
            "canonical_elapsed_sec": canonical_result.summary["canonical_elapsed_sec"],
            "stream_word_count": canonical_result.summary["stream_word_count"],
            "total_stream_word_count": canonical_result.summary["total_stream_word_count"],
            "canonical_total_words_per_sec": canonical_result.summary.get("canonical_total_words_per_sec", 0.0),
            "throughput_encode_words_per_sec": canonical_result.summary["throughput_encode_words_per_sec"],
            "throughput_decode_words_per_sec": canonical_result.summary["throughput_decode_words_per_sec"],
            "canonical_stream_hash": canonical_result.summary["stream_hash"],
            "word_unit": "imc_stream_words",
            "kernel_backend": canonical_result.summary["kernel_backend"],
            "kernel_backend_origin": canonical_result.summary["kernel_backend_origin"],
            "kernel_backend_native": canonical_result.summary["kernel_backend_native"],
            "kernel_backend_compiled_extension": canonical_result.summary["kernel_backend_compiled_extension"],
            "kernel_backend_fallback_used": canonical_result.summary["kernel_backend_fallback_used"],
            "kernel_backend_payload_layout": canonical_result.summary["kernel_backend_payload_layout"],
            "kernel_backend_ffi_contract_version": canonical_result.summary["kernel_backend_ffi_contract_version"],
            "kernel_backend_build_profile": canonical_result.summary["kernel_backend_build_profile"],
            "kernel_backend_module_name": canonical_result.summary["kernel_backend_module_name"],
            "kernel_backend_module_file": canonical_result.summary["kernel_backend_module_file"],
            "kernel_backend_module_version": canonical_result.summary["kernel_backend_module_version"],
            "rust_crate_path": canonical_result.summary["rust_crate_path"],
            "rust_extension_module": canonical_result.summary["rust_extension_module"],
        },
        "classic_comet": {
            "project_status": classic_check.status,
            "project_name": classic_check.resolved_name or DEFAULT_CLASSIC_PROJECT,
            "project_id": classic_check.resolved_id or "",
            "project_slug": classic_check.resolved_slug or "",
            "experiment_key": comet_identity["experiment_key"],
            "experiment_url": comet_identity["experiment_url"],
        },
        "opik": {
            "project_status": opik_check.status,
            "project_name": opik_check.resolved_name or DEFAULT_OPIK_PROJECT,
            "project_id": opik_check.resolved_id or "",
            "project_url": opik_check.url or "",
            "trace_id": opik_trace_id,
            "trace_url": opik_trace_url,
            "proof_reference_mode": proof_reference_mode,
        },
        "live_urls": {
            "classic_comet_experiment_url": comet_identity["experiment_url"],
            "opik_trace_url": opik_trace_url,
            "opik_project_url": opik_check.url or "",
        },
        "validation": {
            "pytest": {
                "return_code": pytest_result.returncode,
                "tests_total": pytest_counts["tests_total"],
                "tests_passed": pytest_counts["tests_passed"],
                "tests_failed": pytest_counts["tests_failed"],
            },
            "dirty_data": {
                "sensation_regression_return_code": sensation_result.returncode,
                "integrated_fidelity_return_code": fidelity_result.returncode,
                "cross_modal_roundtrip_return_code": cross_modal_result.returncode,
            },
            "benchmark_return_code": benchmark_result.returncode,
            "determinism_hash_match": det_match,
            "determinism_probe_id": probe_id,
            "determinism_hashes": [hash_a, hash_b],
            "stream_valid": canonical_result.summary["stream_valid"],
            "modality_coverage_all": canonical_result.summary["modality_coverage_all"],
            "voice_capability_mode": canonical_result.summary["voice_capability_mode"],
            "kernel_backend_native": canonical_result.summary["kernel_backend_native"],
            "kernel_backend_compiled_extension": canonical_result.summary["kernel_backend_compiled_extension"],
            "kernel_backend_fallback_used": canonical_result.summary["kernel_backend_fallback_used"],
        },
        "benchmark": {
            "run_id": benchmark_summary.get("benchmark_run_id", ""),
            "git_commit": benchmark_summary.get("benchmark_git_commit", ""),
            "metric_file_count": benchmark_summary.get("benchmark_metric_files", 0),
            "scenario_count": benchmark_summary.get("benchmark_scenario_count", 0),
            "all_deterministic": benchmark_summary.get("benchmark_all_deterministic", 0),
            "scenario_rows": benchmark_summary.get("scenario_rows", []),
            "metric_file_paths": benchmark_summary.get("metric_file_paths", []),
            "metric_names": benchmark_summary.get("metric_names", []),
        },
        "paths": {
            "env_check_log": str(env_check_path),
            "run_log": str(run_log_path),
            "proof_manifest": str(PROOF_MANIFEST_PATH),
            "benchmark_report": str(BENCHMARK_REPORT_PATH),
            "hotspot_profile": str(HOTSPOT_PROFILE_PATH),
            "benchmark_metrics_dir": str(BENCHMARK_METRICS_DIR),
            "telemetry_log": str(BENCHMARK_TELEMETRY),
            "rust_crate_path": canonical_result.summary["rust_crate_path"],
            "kernel_backend_module_file": canonical_result.summary["kernel_backend_module_file"],
        },
        "metric_names_landed": metric_names,
    }


def main() -> int:
    args = _parse_args()
    workspace = os.environ.get("COMET_WORKSPACE") or os.environ.get("OPIK_WORKSPACE") or DEFAULT_WORKSPACE
    opik_host = os.environ.get("OPIK_URL_OVERRIDE", DEFAULT_OPIK_URL)
    classic_remote_enabled = _remote_logging_enabled(
        enable=bool(args.enable_classic_comet),
        disable=bool(args.disable_classic_comet),
    )
    opik_remote_enabled = _remote_logging_enabled(
        enable=bool(args.enable_opik),
        disable=bool(args.disable_opik),
    )

    classic_check = (
        _verify_classic_comet_project(workspace=workspace, expected_name=DEFAULT_CLASSIC_PROJECT)
        if classic_remote_enabled
        else _disabled_project_check("classic", "disabled by release-default local-only mode")
    )
    opik_check = (
        _verify_opik_project(workspace=workspace, expected_name=DEFAULT_OPIK_PROJECT, host=opik_host)
        if opik_remote_enabled
        else _disabled_project_check("opik", "disabled by release-default local-only mode")
    )
    _write_env_check(
        args.env_check_out,
        workspace=workspace,
        classic_check=classic_check,
        opik_check=opik_check,
        classic_remote_enabled=classic_remote_enabled,
        opik_remote_enabled=opik_remote_enabled,
    )

    run_name = f"IMC-Canonical-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    comet_adapter = ClassicCometAdapter.create(
        project_check=classic_check,
        workspace=workspace,
        run_name=run_name,
        disabled=not classic_remote_enabled,
    )
    opik_adapter = OpikAdapter.create(
        project_check=opik_check,
        workspace=workspace,
        disabled=not opik_remote_enabled,
    )

    trace = opik_adapter.start_trace(
        name="canonical-promotion",
        metadata={
            "run_kind": "canonical-promotion",
            "workspace": workspace,
            "classic_project_status": classic_check.status,
            "opik_project_status": opik_check.status,
        },
        input_payload={"benchmark_profile": args.benchmark_profile},
    )

    subprocess_env = _subprocess_env()
    pytest_span = trace.span(name="pytest_suite", metadata={"phase": "validation"}) if trace is not None else None
    pytest_result = _run_command(
        label="pytest",
        cmd=[sys.executable, "-m", "pytest", "tests", "tests_phase3", "-q"],
        cwd=CODE_ROOT,
        env=subprocess_env,
    )
    pytest_counts = _parse_pytest_counts(pytest_result.output)
    if pytest_span is not None:
        pytest_span.end(output={**pytest_counts, "returncode": pytest_result.returncode})

    dirty_span = trace.span(name="dirty_data_suite", metadata={"phase": "validation"}) if trace is not None else None
    sensation_result = _run_command(
        label="sensation_regression",
        cmd=[sys.executable, str(CODE_ROOT / "tests" / "test_sensation_regression.py")],
        cwd=CODE_ROOT,
        env=subprocess_env,
    )
    fidelity_result = _run_command(
        label="integrated_fidelity",
        cmd=[sys.executable, str(CODE_ROOT / "tests" / "test_integrated_fidelity.py")],
        cwd=CODE_ROOT,
        env=subprocess_env,
    )
    cross_modal_result = _run_command(
        label="cross_modal_roundtrip",
        cmd=[sys.executable, str(CODE_ROOT / "tests" / "test_cross_modal_roundtrip.py")],
        cwd=CODE_ROOT,
        env=subprocess_env,
    )
    if dirty_span is not None:
        dirty_span.end(
            output={
                "sensation_regression_rc": sensation_result.returncode,
                "integrated_fidelity_rc": fidelity_result.returncode,
                "cross_modal_roundtrip_rc": cross_modal_result.returncode,
            }
        )

    benchmark_span = trace.span(name="benchmark_suite", metadata={"phase": "validation"}) if trace is not None else None
    benchmark_result = _run_command(
        label="benchmarks",
        cmd=[
            sys.executable,
            str(CODE_ROOT / "benchmarks" / "run_benchmarks.py"),
            "--profile",
            str(args.benchmark_profile),
            "--artifact-root",
            str(BENCHMARK_ARTIFACT_ROOT),
            "--output-dir",
            str(BENCHMARK_METRICS_DIR),
            "--telemetry-out",
            str(BENCHMARK_TELEMETRY),
        ],
        cwd=CODE_ROOT,
        env=subprocess_env,
    )
    benchmark_summary = _collect_benchmark_summary(BENCHMARK_METRICS_DIR)
    if benchmark_span is not None:
        benchmark_span.end(output={**benchmark_summary, "returncode": benchmark_result.returncode})

    det_match, hash_a, hash_b, probe_id = _determinism_hash_match()
    canonical_result = _run_canonical_with_cpu_gate(trace)
    cpu_count = max(1, int(os.cpu_count() or 1))
    canonical_saturated_run_of_record = 1 if (
        cpu_count == 1
        or canonical_result.rerun_workers == cpu_count
        or float(canonical_result.summary["cpu_core_multiplier"]) >= cpu_count * 0.8
    ) else 0
    opik_trace_id = str(getattr(trace, "id", "") or "")
    opik_trace_url = opik_adapter.get_trace_url(opik_trace_id)
    proof_reference_mode = (
        "native_opik_attachments_with_explicit_reference_bundle"
        if trace is not None and opik_adapter.enabled
        else "local_reference_bundle_only"
    )
    proof_span = (
        trace.span(
            name="proof_bundle",
            metadata={
                "phase": "proof",
                "reference_mode": proof_reference_mode,
                "benchmark_metric_files": benchmark_summary["benchmark_metric_files"],
            },
        )
        if trace is not None
        else None
    )
    proof_attachment_paths = [
        args.env_check_out,
        BENCHMARK_REPORT_PATH,
        HOTSPOT_PROFILE_PATH,
        BENCHMARK_TELEMETRY,
        *(Path(path) for path in benchmark_summary.get("metric_file_paths", [])),
    ]
    attachment_result = (
        opik_adapter.upload_attachments(
            entity_type="span",
            entity_id=str(proof_span.id),
            paths=proof_attachment_paths,
        )
        if proof_span is not None
        else AttachmentUploadResult(
            status="disabled",
            requested_count=0,
            uploaded_count=0,
            verified_count=0,
        )
    )
    comet_identity = comet_adapter.identity()
    classic_remote_requested = classic_remote_enabled and bool((os.environ.get("COMET_API_KEY") or "").strip())
    opik_remote_requested = opik_remote_enabled and bool(_opik_api_key())
    classic_logging_ok = (
        1
        if not classic_remote_enabled
        else 1
        if not classic_remote_requested
        else 1 if comet_adapter.enabled and classic_check.status in {"EXISTS", "CREATED"} else 0
    )
    opik_logging_ok = (
        1
        if not opik_remote_enabled
        else 1
        if not opik_remote_requested
        else 1 if trace is not None and opik_adapter.enabled and opik_check.status in {"EXISTS", "CREATED"} else 0
    )
    opik_reference_bundle_logged = 1 if (trace is not None or not opik_remote_enabled or not opik_remote_requested) else 0
    base_proof_bundle_complete = _proof_bundle_complete(proof_attachment_paths)
    metrics: dict[str, int | float] = {
        "tests_total": pytest_counts["tests_total"],
        "tests_passed": pytest_counts["tests_passed"],
        "tests_failed": pytest_counts["tests_failed"],
        "sensation_regression_ok": 1 if sensation_result.returncode == 0 else 0,
        "integrated_fidelity_ok": 1 if fidelity_result.returncode == 0 else 0,
        "cross_modal_roundtrip_ok": 1 if cross_modal_result.returncode == 0 else 0,
        "benchmark_return_code": benchmark_result.returncode,
        "benchmark_metric_files": int(benchmark_summary["benchmark_metric_files"]),
        "benchmark_metric_scalar_count": len(benchmark_summary["scenario_metrics"]),
        "benchmark_scenario_count": int(benchmark_summary["benchmark_scenario_count"]),
        "benchmark_all_deterministic": int(benchmark_summary["benchmark_all_deterministic"]),
        "determinism_hash_match": det_match,
        "stream_word_count_smoke": int(canonical_result.summary["stream_word_count"]),
        "canonical_total_stream_word_count": int(canonical_result.summary["total_stream_word_count"]),
        "canonical_elapsed_sec": float(canonical_result.summary["canonical_elapsed_sec"]),
        "canonical_total_words_per_sec": float(canonical_result.summary.get("canonical_total_words_per_sec", 0.0)),
        "throughput_encode_words_per_sec": float(canonical_result.summary["throughput_encode_words_per_sec"]),
        "throughput_decode_words_per_sec": float(canonical_result.summary["throughput_decode_words_per_sec"]),
        "single_core_prepass_elapsed_sec": float(canonical_result.summary.get("single_core_prepass_elapsed_sec", 0.0)),
        "single_core_prepass_total_words_per_sec": float(
            canonical_result.summary.get("single_core_prepass_total_words_per_sec", 0.0)
        ),
        "single_core_prepass_encode_words_per_sec": float(
            canonical_result.summary.get("single_core_prepass_encode_words_per_sec", 0.0)
        ),
        "single_core_prepass_decode_words_per_sec": float(
            canonical_result.summary.get("single_core_prepass_decode_words_per_sec", 0.0)
        ),
        "canonical_measurement_steady_state_batch": 1
        if canonical_result.summary.get("measurement_mode") == CANONICAL_STEADY_STATE_MEASUREMENT_MODE
        else 0,
        "canonical_stream_valid": 1 if canonical_result.summary["stream_valid"] else 0,
        "modality_coverage_count": int(canonical_result.summary["modality_coverage_count"]),
        "modality_coverage_all": int(canonical_result.summary["modality_coverage_all"]),
        "canonical_cpu_core_multiplier": float(canonical_result.summary["cpu_core_multiplier"]),
        "canonical_reran_for_cpu_saturation": 1 if canonical_result.reran_for_cpu_saturation else 0,
        "canonical_parallel_workers": canonical_result.rerun_workers,
        "canonical_parallel_batch_iterations": int(canonical_result.summary.get("parallel_batch_iterations", 1)),
        "canonical_saturated_run_of_record": canonical_saturated_run_of_record,
        "kernel_backend_native": int(canonical_result.summary["kernel_backend_native"]),
        "kernel_backend_compiled_extension": int(canonical_result.summary["kernel_backend_compiled_extension"]),
        "kernel_backend_fallback_used": int(canonical_result.summary["kernel_backend_fallback_used"]),
        "kernel_backend_normal_word_count": int(canonical_result.summary["kernel_backend_normal_word_count"]),
        "classic_remote_enabled": 1 if classic_remote_enabled else 0,
        "classic_logging_enabled": 1 if comet_adapter.enabled else 0,
        "classic_logging_ok": classic_logging_ok,
        "opik_remote_enabled": 1 if opik_remote_enabled else 0,
        "opik_logging_enabled": 1 if opik_adapter.enabled and trace is not None else 0,
        "opik_logging_ok": opik_logging_ok,
        "opik_trace_logged": 1 if trace is not None else 0,
        "opik_reference_bundle_logged": opik_reference_bundle_logged,
        "opik_native_attachment_requested_count": attachment_result.requested_count,
        "opik_native_attachment_uploaded_count": attachment_result.uploaded_count,
        "opik_native_attachment_verified_count": attachment_result.verified_count,
        "opik_native_attachment_verified": 1 if attachment_result.status == "verified" else 0,
        "benchmark_report_present": 1 if BENCHMARK_REPORT_PATH.exists() else 0,
        "hotspot_profile_present": 1 if HOTSPOT_PROFILE_PATH.exists() else 0,
        "telemetry_log_present": 1 if BENCHMARK_TELEMETRY.exists() else 0,
        "proof_manifest_present": 0,
        "proof_bundle_complete": 0,
        "proof_visibility_ok": 1 if base_proof_bundle_complete and opik_reference_bundle_logged else 0,
    }
    metrics.update(benchmark_summary["scenario_metrics"])
    for key, value in canonical_result.summary["modality_counts"].items():
        metrics[f"count_{key}"] = int(value)
    history_project_name = (
        classic_check.resolved_slug
        or (classic_check.resolved_name or DEFAULT_CLASSIC_PROJECT).strip().lower().replace(" ", "-")
    )
    curated_surface = _build_curated_surface(
        workspace=workspace,
        project_name=history_project_name,
        pytest_counts=pytest_counts,
        canonical_result=canonical_result,
        benchmark_telemetry_path=BENCHMARK_TELEMETRY,
    )
    metrics.update(curated_surface.final_metrics)

    provisional_ok = all(
        (
            pytest_result.returncode == 0,
            sensation_result.returncode == 0,
            fidelity_result.returncode == 0,
            cross_modal_result.returncode == 0,
            benchmark_result.returncode == 0,
            det_match == 1,
            canonical_result.summary["stream_valid"],
            canonical_result.summary["modality_coverage_all"] == 1,
            canonical_result.summary["voice_capability_mode"] == "full",
            canonical_result.summary["kernel_backend_native"] == 1,
            canonical_result.summary["kernel_backend_compiled_extension"] == 1,
            canonical_result.summary["kernel_backend_fallback_used"] == 0,
            canonical_saturated_run_of_record == 1,
            classic_logging_ok == 1,
            opik_logging_ok == 1,
            metrics["proof_visibility_ok"] == 1,
        )
    )
    provisional_status = "PASS" if provisional_ok else "FAIL"
    provisional_metric_names = sorted(set(metrics) | set(curated_surface.metric_names))
    provisional_manifest = _build_proof_manifest(
        status=provisional_status,
        workspace=workspace,
        run_name=run_name,
        classic_check=classic_check,
        opik_check=opik_check,
        comet_identity=comet_identity,
        opik_trace_id=opik_trace_id,
        opik_trace_url=opik_trace_url,
        benchmark_summary=benchmark_summary,
        canonical_result=canonical_result,
        pytest_counts=pytest_counts,
        pytest_result=pytest_result,
        sensation_result=sensation_result,
        fidelity_result=fidelity_result,
        cross_modal_result=cross_modal_result,
        benchmark_result=benchmark_result,
        det_match=det_match,
        hash_a=hash_a,
        hash_b=hash_b,
        probe_id=probe_id,
        metric_names=provisional_metric_names,
        env_check_path=args.env_check_out,
        run_log_path=args.log_out,
        proof_reference_mode=proof_reference_mode,
    )
    _write_json(PROOF_MANIFEST_PATH, provisional_manifest)

    required_proof_paths = proof_attachment_paths + [PROOF_MANIFEST_PATH]
    metrics["proof_manifest_present"] = 1 if PROOF_MANIFEST_PATH.exists() else 0
    metrics["proof_bundle_complete"] = _proof_bundle_complete(required_proof_paths)
    metrics["proof_visibility_ok"] = 1 if (
        metrics["proof_bundle_complete"] == 1
        and opik_reference_bundle_logged == 1
        and metrics["benchmark_report_present"] == 1
        and metrics["hotspot_profile_present"] == 1
        and metrics["telemetry_log_present"] == 1
    ) else 0

    overall_ok = all(
        (
            pytest_result.returncode == 0,
            sensation_result.returncode == 0,
            fidelity_result.returncode == 0,
            cross_modal_result.returncode == 0,
            benchmark_result.returncode == 0,
            det_match == 1,
            canonical_result.summary["stream_valid"],
            canonical_result.summary["modality_coverage_all"] == 1,
            canonical_result.summary["voice_capability_mode"] == "full",
            canonical_result.summary["kernel_backend_native"] == 1,
            canonical_result.summary["kernel_backend_compiled_extension"] == 1,
            canonical_result.summary["kernel_backend_fallback_used"] == 0,
            canonical_saturated_run_of_record == 1,
            classic_logging_ok == 1,
            opik_logging_ok == 1,
            metrics["proof_visibility_ok"] == 1,
        )
    )
    status = "PASS" if overall_ok else "FAIL"
    metric_names = sorted(set(metrics) | set(curated_surface.metric_names))

    for key, value in (
        ("classic_project_status", classic_check.status),
        ("classic_project_name", classic_check.resolved_name or ""),
        ("classic_project_id", classic_check.resolved_id or ""),
        ("classic_project_slug", classic_check.resolved_slug or ""),
        ("opik_project_status", opik_check.status),
        ("opik_project_name", opik_check.resolved_name or ""),
        ("opik_project_id", opik_check.resolved_id or ""),
        ("opik_project_url", opik_check.url or ""),
        ("opik_trace_id", opik_trace_id),
        ("opik_trace_url", opik_trace_url),
        ("opik_attachment_status", attachment_result.status),
        ("proof_reference_mode", proof_reference_mode),
        ("proof_manifest_path", str(PROOF_MANIFEST_PATH)),
        ("phase6_env_check_path", str(args.env_check_out)),
        ("phase6_run_log_path", str(args.log_out)),
        ("benchmark_run_id", str(benchmark_summary.get("benchmark_run_id", ""))),
        ("benchmark_report_path", str(BENCHMARK_REPORT_PATH)),
        ("hotspot_profile_path", str(HOTSPOT_PROFILE_PATH)),
        ("benchmark_metrics_dir", str(BENCHMARK_METRICS_DIR)),
        ("benchmark_telemetry_log_path", str(BENCHMARK_TELEMETRY)),
        ("canonical_stream_hash", canonical_result.summary["stream_hash"]),
        ("voice_capability_mode", canonical_result.summary["voice_capability_mode"]),
        ("kernel_backend", canonical_result.summary["kernel_backend"]),
        ("kernel_backend_origin", canonical_result.summary["kernel_backend_origin"]),
        ("kernel_backend_module_name", canonical_result.summary["kernel_backend_module_name"]),
        ("kernel_backend_module_file", canonical_result.summary["kernel_backend_module_file"]),
        ("kernel_backend_module_version", canonical_result.summary["kernel_backend_module_version"]),
        ("rust_crate_path", canonical_result.summary["rust_crate_path"]),
        ("rust_extension_module", canonical_result.summary["rust_extension_module"]),
        ("release_default_local_only", 1),
        ("classic_remote_enabled", 1 if classic_remote_enabled else 0),
        ("opik_remote_enabled", 1 if opik_remote_enabled else 0),
        ("canonical_measurement_mode", canonical_result.summary.get("measurement_mode", "")),
        ("canonical_measurement_scope", canonical_result.summary.get("measurement_scope", "")),
        (
            "single_core_prepass_measurement_mode",
            canonical_result.summary.get("single_core_prepass_measurement_mode", ""),
        ),
        (
            "single_core_prepass_measurement_scope",
            canonical_result.summary.get("single_core_prepass_measurement_scope", ""),
        ),
        ("determinism_probe_id", probe_id),
        ("determinism_hash_a", hash_a),
        ("determinism_hash_b", hash_b),
    ):
        comet_adapter.log_parameter(key, value)
    for key, value in curated_surface.parameter_values.items():
        comet_adapter.log_parameter(key, value)
    for series_map in (curated_surface.cross_run_series, curated_surface.inrun_series, curated_surface.benchmark_series):
        for metric_name, points in series_map.items():
            for step, value in points:
                comet_adapter.log_metric(metric_name, value, step=step)
    comet_adapter.log_metrics(metrics)
    comet_adapter.log_text(
        "\n".join(
            comet_adapter.notes
            + opik_adapter.notes
            + [
                f"proof_reference_mode={proof_reference_mode}",
                f"opik_attachment_status={attachment_result.status}",
                f"metric_names_landed={','.join(metric_names)}",
            ]
        )
    )
    comet_finish = comet_adapter.finish()

    final_manifest = _build_proof_manifest(
        status=status,
        workspace=workspace,
        run_name=run_name,
        classic_check=classic_check,
        opik_check=opik_check,
        comet_identity=comet_finish,
        opik_trace_id=opik_trace_id,
        opik_trace_url=opik_trace_url,
        benchmark_summary=benchmark_summary,
        canonical_result=canonical_result,
        pytest_counts=pytest_counts,
        pytest_result=pytest_result,
        sensation_result=sensation_result,
        fidelity_result=fidelity_result,
        cross_modal_result=cross_modal_result,
        benchmark_result=benchmark_result,
        det_match=det_match,
        hash_a=hash_a,
        hash_b=hash_b,
        probe_id=probe_id,
        metric_names=metric_names,
        env_check_path=args.env_check_out,
        run_log_path=args.log_out,
        proof_reference_mode=proof_reference_mode,
    )
    _write_json(PROOF_MANIFEST_PATH, final_manifest)

    run_lines = [
        "IMC DUAL LOGGING RUN",
        f"status={status}",
        "release_default_local_only=1",
        "run_of_record_type=saturated_canonical",
        f"classic_remote_enabled={1 if classic_remote_enabled else 0}",
        f"opik_remote_enabled={1 if opik_remote_enabled else 0}",
        f"canonical_measurement_mode={canonical_result.summary.get('measurement_mode', CANONICAL_STEADY_STATE_MEASUREMENT_MODE)}",
        f"canonical_measurement_scope={canonical_result.summary.get('measurement_scope', 'saturated_run_of_record')}",
        f"single_core_prepass_reported={int(canonical_result.summary.get('single_core_prepass_reported', 0))}",
        f"single_core_prepass_measurement_mode={canonical_result.summary.get('single_core_prepass_measurement_mode', CANONICAL_PREPASS_MEASUREMENT_MODE)}",
        f"single_core_prepass_measurement_scope={canonical_result.summary.get('single_core_prepass_measurement_scope', 'single_stream_prepass')}",
        f"classic_project_status={classic_check.status}",
        f"classic_project_name={classic_check.resolved_name or '(unset)'}",
        f"classic_project_id={classic_check.resolved_id or '(unset)'}",
        f"classic_project_slug={classic_check.resolved_slug or '(unset)'}",
        f"classic_handshake_error={classic_check.handshake_error or '(none)'}",
        f"opik_project_status={opik_check.status}",
        f"opik_project_name={opik_check.resolved_name or '(unset)'}",
        f"opik_project_id={opik_check.resolved_id or '(unset)'}",
        f"opik_project_url={opik_check.url or '(unset)'}",
        f"opik_trace_id={opik_trace_id or '(unset)'}",
        f"opik_trace_url={opik_trace_url or '(unset)'}",
        f"opik_handshake_error={opik_check.handshake_error or '(none)'}",
        f"proof_reference_mode={proof_reference_mode}",
        f"proof_manifest_path={PROOF_MANIFEST_PATH}",
        f"benchmark_report_path={BENCHMARK_REPORT_PATH}",
        f"hotspot_profile_path={HOTSPOT_PROFILE_PATH}",
        f"benchmark_metrics_dir={BENCHMARK_METRICS_DIR}",
        f"telemetry_log_path={BENCHMARK_TELEMETRY}",
        f"kernel_backend={canonical_result.summary['kernel_backend']}",
        f"kernel_backend_origin={canonical_result.summary['kernel_backend_origin']}",
        f"kernel_backend_native={canonical_result.summary['kernel_backend_native']}",
        f"kernel_backend_compiled_extension={canonical_result.summary['kernel_backend_compiled_extension']}",
        f"kernel_backend_fallback_used={canonical_result.summary['kernel_backend_fallback_used']}",
        f"kernel_backend_payload_layout={canonical_result.summary['kernel_backend_payload_layout']}",
        f"kernel_backend_ffi_contract_version={canonical_result.summary['kernel_backend_ffi_contract_version']}",
        f"kernel_backend_build_profile={canonical_result.summary['kernel_backend_build_profile']}",
        f"kernel_backend_module_name={canonical_result.summary['kernel_backend_module_name']}",
        f"kernel_backend_module_file={canonical_result.summary['kernel_backend_module_file']}",
        f"kernel_backend_module_version={canonical_result.summary['kernel_backend_module_version']}",
        f"rust_crate_path={canonical_result.summary['rust_crate_path']}",
        f"rust_extension_module={canonical_result.summary['rust_extension_module']}",
        f"opik_attachment_status={attachment_result.status}",
        f"opik_attachment_requested_count={attachment_result.requested_count}",
        f"opik_attachment_uploaded_count={attachment_result.uploaded_count}",
        f"opik_attachment_verified_count={attachment_result.verified_count}",
        f"classic_logging_enabled={1 if comet_adapter.enabled else 0}",
        f"opik_logging_enabled={1 if opik_adapter.enabled else 0}",
        *(f"{key}={value}" for key, value in metrics.items()),
        f"pytest_return_code={pytest_result.returncode}",
        f"sensation_regression_return_code={sensation_result.returncode}",
        f"integrated_fidelity_return_code={fidelity_result.returncode}",
        f"cross_modal_roundtrip_return_code={cross_modal_result.returncode}",
        f"benchmark_return_code={benchmark_result.returncode}",
        f"benchmark_run_id={benchmark_summary.get('benchmark_run_id', '') or '(unset)'}",
        f"canonical_stream_hash={canonical_result.summary['stream_hash']}",
        f"canonical_cpu_core_multiplier={canonical_result.summary['cpu_core_multiplier']}",
        f"canonical_elapsed_sec={canonical_result.summary['canonical_elapsed_sec']}",
        f"canonical_reran_for_cpu_saturation={1 if canonical_result.reran_for_cpu_saturation else 0}",
        f"canonical_parallel_workers={canonical_result.rerun_workers}",
        f"canonical_parallel_batch_iterations={int(canonical_result.summary.get('parallel_batch_iterations', 1))}",
        f"single_core_prepass_elapsed_sec={canonical_result.summary.get('single_core_prepass_elapsed_sec', 0.0)}",
        f"single_core_prepass_total_words_per_sec={canonical_result.summary.get('single_core_prepass_total_words_per_sec', 0.0)}",
        f"single_core_prepass_encode_words_per_sec={canonical_result.summary.get('single_core_prepass_encode_words_per_sec', 0.0)}",
        f"single_core_prepass_decode_words_per_sec={canonical_result.summary.get('single_core_prepass_decode_words_per_sec', 0.0)}",
        f"canonical_total_words_per_sec={canonical_result.summary.get('canonical_total_words_per_sec', 0.0)}",
        f"throughput_encode_words_per_sec={canonical_result.summary['throughput_encode_words_per_sec']}",
        f"throughput_decode_words_per_sec={canonical_result.summary['throughput_decode_words_per_sec']}",
        f"determinism_probe_id={probe_id}",
        f"determinism_hash_a={hash_a}",
        f"determinism_hash_b={hash_b}",
        f"comet_experiment_key={comet_finish['experiment_key'] or '(unset)'}",
        f"comet_experiment_url={comet_finish['experiment_url'] or '(unset)'}",
        "PYTEST_OUTPUT_HEAD",
        _trim_output(pytest_result.output),
        "SENSATION_REGRESSION_OUTPUT_HEAD",
        _trim_output(sensation_result.output),
        "INTEGRATED_FIDELITY_OUTPUT_HEAD",
        _trim_output(fidelity_result.output),
        "CROSS_MODAL_ROUNDTRIP_OUTPUT_HEAD",
        _trim_output(cross_modal_result.output),
        "BENCHMARK_OUTPUT_HEAD",
        _trim_output(benchmark_result.output),
    ]

    args.log_out.parent.mkdir(parents=True, exist_ok=True)
    args.log_out.write_text("\n".join(run_lines) + "\n", encoding="utf-8")

    if trace is not None and proof_span is not None:
        proof_span.end(
            output={
                "proof_manifest_path": str(PROOF_MANIFEST_PATH),
                "run_log_path": str(args.log_out),
                "benchmark_report_path": str(BENCHMARK_REPORT_PATH),
                "hotspot_profile_path": str(HOTSPOT_PROFILE_PATH),
                "telemetry_log_path": str(BENCHMARK_TELEMETRY),
                "metric_file_paths": benchmark_summary.get("metric_file_paths", []),
                "opik_attachment_status": attachment_result.status,
                "opik_attachment_requested_count": attachment_result.requested_count,
                "opik_attachment_uploaded_count": attachment_result.uploaded_count,
                "opik_attachment_verified_count": attachment_result.verified_count,
                "opik_trace_url": opik_trace_url,
            }
        )
        trace.end(
            metadata={
                "canonical_summary": canonical_result.summary,
                "pytest_counts": pytest_counts,
                "benchmark_summary": {
                    "run_id": benchmark_summary.get("benchmark_run_id", ""),
                    "scenario_count": benchmark_summary.get("benchmark_scenario_count", 0),
                    "metric_file_count": benchmark_summary.get("benchmark_metric_files", 0),
                    "all_deterministic": benchmark_summary.get("benchmark_all_deterministic", 0),
                },
                "proof_bundle": {
                    "manifest_path": str(PROOF_MANIFEST_PATH),
                    "run_log_path": str(args.log_out),
                    "reference_mode": proof_reference_mode,
                    "attachment_status": attachment_result.status,
                    "attachment_verified_count": attachment_result.verified_count,
                },
                "kernel_backend": {
                    "backend": canonical_result.summary["kernel_backend"],
                    "origin": canonical_result.summary["kernel_backend_origin"],
                    "native": canonical_result.summary["kernel_backend_native"],
                    "compiled_extension": canonical_result.summary["kernel_backend_compiled_extension"],
                    "fallback_used": canonical_result.summary["kernel_backend_fallback_used"],
                    "module_name": canonical_result.summary["kernel_backend_module_name"],
                    "module_file": canonical_result.summary["kernel_backend_module_file"],
                    "module_version": canonical_result.summary["kernel_backend_module_version"],
                },
                "determinism_probe_id": probe_id,
                "determinism_hash_a": hash_a,
                "determinism_hash_b": hash_b,
                "classic_project_status": classic_check.status,
                "opik_project_status": opik_check.status,
                "classic_experiment_url": comet_finish["experiment_url"],
                "opik_trace_url": opik_trace_url,
                "status": status,
            },
            output={
                "pytest_return_code": pytest_result.returncode,
                "sensation_regression_return_code": sensation_result.returncode,
                "integrated_fidelity_return_code": fidelity_result.returncode,
                "cross_modal_roundtrip_return_code": cross_modal_result.returncode,
                "benchmark_return_code": benchmark_result.returncode,
                "canonical_stream_hash": canonical_result.summary["stream_hash"],
                "canonical_elapsed_sec": canonical_result.summary["canonical_elapsed_sec"],
                "canonical_total_words_per_sec": canonical_result.summary.get("canonical_total_words_per_sec", 0.0),
                "throughput_encode_words_per_sec": canonical_result.summary["throughput_encode_words_per_sec"],
                "throughput_decode_words_per_sec": canonical_result.summary["throughput_decode_words_per_sec"],
            },
            thread_id=DEFAULT_THREAD_ID,
        )
    opik_adapter.finish()
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

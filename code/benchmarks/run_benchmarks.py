#!/usr/bin/env python3
from __future__ import annotations

import argparse
import cProfile
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import pstats
import subprocess
import sys
import time
import tracemalloc
from typing import Any
import unicodedata

import numpy as np


SCRIPT_PATH = Path(__file__).resolve()
CODE_ROOT = SCRIPT_PATH.parents[1]
V0_ROOT = CODE_ROOT.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from zpe_multimodal import decode, encode
from zpe_multimodal.core.imc import IMCDecoder, IMCEncoder


REQUIRED_METRIC_KEYS = (
    "run_id",
    "timestamp_utc",
    "git_commit",
    "scenario",
    "dataset_or_fixture",
    "throughput_tokens_per_sec",
    "latency_ms_p50",
    "latency_ms_p95",
    "peak_memory_mb",
    "deterministic",
    "notes",
)

ALLOWED_PROFILES = ("baseline", "medium", "heavy")
PROTOCOL_VERSION = "WS3_BENCHMARK_PROTOCOL_2026-03-05"
PROGRESSIVE_EVENT_PREFIX = "ws3.progressive"


@dataclass(frozen=True)
class Scenario:
    scenario: str
    category: str
    profile: str
    kind: str
    dataset_or_fixture: str
    iterations: int
    warmup_iterations: int
    text: str
    bpe_tokens: tuple[int, ...] | None = None
    image_size: tuple[int, int] | None = None
    svg: str | None = None
    music_fixture: str | None = None
    voice_fixture: str | None = None


class ScenarioError(RuntimeError):
    pass


class ProgressiveTelemetry:
    def __init__(self, *, run_id: str, output_path: Path, experiment: Any | None) -> None:
        self.run_id = run_id
        self.output_path = output_path
        self.experiment = experiment
        self._event_index = 0
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text("", encoding="utf-8")

    def emit(self, *, event_type: str, phase: str, **payload: Any) -> None:
        self._event_index += 1
        event: dict[str, Any] = {
            "timestamp_utc": _utc_now(),
            "run_id": self.run_id,
            "event_index": self._event_index,
            "event_type": event_type,
            "phase": phase,
        }
        event.update({k: v for k, v in payload.items() if v is not None})
        line = json.dumps(event, sort_keys=True)
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

        if self.experiment is not None:
            try:
                event_key = f"{PROGRESSIVE_EVENT_PREFIX}.{self._event_index:04d}"
                self.experiment.log_other(event_key, line)
                self.experiment.log_metric(
                    f"{PROGRESSIVE_EVENT_PREFIX}.event_index",
                    self._event_index,
                    step=self._event_index,
                )
            except Exception:
                pass


def configure_env() -> None:
    os.environ.setdefault("STROKEGRAM_ENABLE_DIAGRAM", "1")
    os.environ.setdefault("STROKEGRAM_ENABLE_MUSIC", "1")
    os.environ.setdefault("STROKEGRAM_ENABLE_VOICE", "1")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"A4-BENCH-{ts}"


def _git_commit() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=V0_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return proc.stdout.strip()
    except Exception:
        return "UNKNOWN"


def _make_comet_experiment(*, run_id: str) -> tuple[Any | None, list[str], bool]:
    notes: list[str] = []
    api_key = os.environ.get("COMET_API_KEY", "").strip()
    workspace = os.environ.get("COMET_WORKSPACE", "").strip()
    project_name = os.environ.get("COMET_PROJECT_NAME", "").strip()
    experiment_name = os.environ.get("COMET_EXPERIMENT_NAME", "").strip()

    if not api_key:
        notes.append("COMET_API_KEY missing; writing local progressive telemetry mirror only.")
        return None, notes, False

    try:
        from comet_ml import Experiment  # type: ignore
    except Exception as exc:
        notes.append(f"COMET_API_KEY set but comet_ml unavailable ({exc}); local mirror only.")
        return None, notes, False

    kwargs: dict[str, Any] = {"api_key": api_key}
    if workspace:
        kwargs["workspace"] = workspace
    if project_name:
        kwargs["project_name"] = project_name

    experiment = Experiment(**kwargs)
    experiment.set_name(experiment_name or f"WS3-{run_id}")
    notes.append("Remote Comet progressive logging enabled.")
    return experiment, notes, True


def _safe_slug(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in name).strip("-").lower()


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * percentile
    low = int(math.floor(rank))
    high = int(math.ceil(rank))
    if low == high:
        return float(ordered[low])
    ratio = rank - low
    return float(ordered[low] + (ordered[high] - ordered[low]) * ratio)


def _canonical_text(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _load_scenarios(scenario_dir: Path) -> list[Scenario]:
    scenario_files = sorted(scenario_dir.glob("*.json"))
    if not scenario_files:
        raise ScenarioError(f"no scenario JSON files found in {scenario_dir}")

    loaded: list[Scenario] = []
    for path in scenario_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ScenarioError(f"scenario file must be a JSON list: {path}")
        for item in payload:
            if not isinstance(item, dict):
                raise ScenarioError(f"scenario entries must be objects: {path}")
            loaded.append(
                Scenario(
                    scenario=str(item["scenario"]),
                    category=str(item["category"]),
                    profile=str(item.get("profile", "baseline")).strip().lower() or "baseline",
                    kind=str(item["kind"]),
                    dataset_or_fixture=str(item["dataset_or_fixture"]),
                    iterations=max(1, int(item.get("iterations", 20))),
                    warmup_iterations=max(0, int(item.get("warmup_iterations", 3))),
                    text=str(item["text"]),
                    bpe_tokens=tuple(int(v) for v in item.get("bpe_tokens", [])) or None,
                    image_size=(
                        int(item["image_size"][0]),
                        int(item["image_size"][1]),
                    )
                    if item.get("image_size")
                    else None,
                    svg=str(item["svg"]) if item.get("svg") else None,
                    music_fixture=str(item["music_fixture"]) if item.get("music_fixture") else None,
                    voice_fixture=str(item["voice_fixture"]) if item.get("voice_fixture") else None,
                )
            )

    if len(loaded) < 10:
        raise ScenarioError(f"expected >= 10 scenarios, found {len(loaded)}")

    invalid = sorted({s.profile for s in loaded if s.profile not in ALLOWED_PROFILES})
    if invalid:
        raise ScenarioError(f"unsupported scenario profiles {invalid}; allowed={ALLOWED_PROFILES}")

    return loaded


def _select_scenarios(loaded: list[Scenario], *, profile: str, scenario_limit: int) -> list[Scenario]:
    selected = [s for s in loaded if profile == "all" or s.profile == profile]
    if scenario_limit > 0:
        selected = selected[:scenario_limit]
    if not selected:
        raise ScenarioError(
            f"no scenarios selected for profile={profile!r} with scenario_limit={scenario_limit}; "
            f"available profiles={ALLOWED_PROFILES}"
        )
    return selected


def _build_gradient_image(height: int, width: int) -> np.ndarray:
    y = np.linspace(0, 255, height, dtype=np.uint8)
    x = np.linspace(255, 0, width, dtype=np.uint8)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :, 0] = np.tile(x, (height, 1))
    img[:, :, 1] = np.tile(y[:, None], (1, width))
    img[:, :, 2] = 127
    return img


def _execute_text_roundtrip(text: str) -> tuple[list[int], str]:
    token_ids = encode(text)
    decoded = decode(token_ids)
    return token_ids, decoded


def _execute_multimodal_roundtrip(scenario: Scenario, *, code_root: Path) -> tuple[list[int], str]:
    encoder = IMCEncoder()
    encoder.add_text(scenario.text)

    if scenario.svg:
        encoder.add_svg(scenario.svg)

    if scenario.music_fixture:
        encoder.add_music(code_root / scenario.music_fixture)

    if scenario.voice_fixture:
        encoder.add_voice(code_root / scenario.voice_fixture)

    if scenario.image_size:
        h, w = scenario.image_size
        encoder.add_image(_build_gradient_image(h, w), bits=3)

    if scenario.bpe_tokens:
        encoder.add_bpe(scenario.bpe_tokens)

    stream = encoder.build()
    result = IMCDecoder().decode(stream)
    return stream, result.text


def _execute_scenario(scenario: Scenario, *, code_root: Path) -> tuple[list[int], str]:
    if scenario.kind == "text":
        return _execute_text_roundtrip(scenario.text)
    if scenario.kind == "multimodal":
        return _execute_multimodal_roundtrip(scenario, code_root=code_root)
    raise ScenarioError(f"unsupported scenario kind: {scenario.kind}")


def _run_scenario(
    scenario: Scenario,
    *,
    run_id: str,
    git_commit: str,
    code_root: Path,
    telemetry: ProgressiveTelemetry | None,
) -> dict[str, Any]:
    for _ in range(scenario.warmup_iterations):
        _execute_scenario(scenario, code_root=code_root)

    if telemetry is not None:
        telemetry.emit(
            event_type="phase_milestone",
            phase="warmup_complete",
            scenario=scenario.scenario,
            profile=scenario.profile,
            warmup_iterations=scenario.warmup_iterations,
        )

    latencies_ms: list[float] = []
    token_counts: list[int] = []
    deterministic_hashes: list[str] = []
    expected_text = _canonical_text(scenario.text)

    tracemalloc.start()
    peak_bytes = 0

    for i in range(scenario.iterations):
        start = time.perf_counter()
        words, decoded = _execute_scenario(scenario, code_root=code_root)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        latencies_ms.append(elapsed_ms)
        token_counts.append(len(words))

        if _canonical_text(decoded) != expected_text:
            raise ScenarioError(
                f"decoded text mismatch in {scenario.scenario}: expected={expected_text!r} got={decoded!r}"
            )

        if i < 5:
            blob = json.dumps(words, separators=(",", ":")).encode("utf-8")
            deterministic_hashes.append(hashlib.sha256(blob).hexdigest())

        _current, peak = tracemalloc.get_traced_memory()
        peak_bytes = max(peak_bytes, int(peak))

    tracemalloc.stop()

    total_latency_sec = sum(latencies_ms) / 1000.0
    total_tokens = sum(token_counts)
    throughput = (float(total_tokens) / total_latency_sec) if total_latency_sec > 0 else 0.0

    metric: dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": _utc_now(),
        "git_commit": git_commit,
        "scenario": scenario.scenario,
        "dataset_or_fixture": scenario.dataset_or_fixture,
        "throughput_tokens_per_sec": round(throughput, 4),
        "latency_ms_p50": round(_percentile(latencies_ms, 0.50), 4),
        "latency_ms_p95": round(_percentile(latencies_ms, 0.95), 4),
        "peak_memory_mb": round(peak_bytes / (1024.0 * 1024.0), 4),
        "deterministic": len(set(deterministic_hashes)) == 1,
        "notes": (
            f"category={scenario.category}; profile={scenario.profile}; kind={scenario.kind}; "
            f"iterations={scenario.iterations}; warmup={scenario.warmup_iterations}; "
            f"determinism_hashes={len(deterministic_hashes)}"
        ),
        "_meta": {
            "category": scenario.category,
            "profile": scenario.profile,
            "kind": scenario.kind,
            "iterations": scenario.iterations,
            "warmup_iterations": scenario.warmup_iterations,
            "mean_tokens": round(total_tokens / max(1, scenario.iterations), 4),
        },
    }

    missing = [key for key in REQUIRED_METRIC_KEYS if key not in metric]
    if missing:
        raise ScenarioError(f"metric missing required keys for {scenario.scenario}: {missing}")

    return metric


def _run_profile(scenarios: list[Scenario], *, code_root: Path, top_n: int) -> list[dict[str, Any]]:
    profiler = cProfile.Profile()
    profiler.enable()
    for scenario in scenarios:
        _execute_scenario(scenario, code_root=code_root)
    profiler.disable()

    stats = pstats.Stats(profiler)
    rows: list[dict[str, Any]] = []
    total_self_time = sum(values[2] for values in stats.stats.values())

    for (filename, lineno, funcname), values in stats.stats.items():
        self_time = float(values[2])
        if self_time <= 0:
            continue
        rows.append(
            {
                "function": funcname,
                "location": f"{Path(filename).name}:{lineno}",
                "self_time_s": round(self_time, 6),
                "wall_time_share_pct": round((self_time / total_self_time) * 100.0, 4) if total_self_time > 0 else 0.0,
            }
        )

    rows.sort(key=lambda item: item["self_time_s"], reverse=True)
    return rows[: max(5, top_n)]


def _write_metric_files(metrics: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for metric in metrics:
        slug = _safe_slug(metric["scenario"])
        out_path = output_dir / f"{slug}.json"
        payload = dict(metric)
        payload.pop("_meta", None)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_benchmark_report(
    *,
    metrics: list[dict[str, Any]],
    report_path: Path,
    run_id: str,
    git_commit: str,
    scenario_dir: Path,
    profile_filter: str,
    protocol_version: str,
) -> None:
    lines = [
        "# A4 Benchmark Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Git commit: `{git_commit}`",
        f"- Timestamp (UTC): `{_utc_now()}`",
        f"- Protocol version: `{protocol_version}`",
        f"- Scenario directory: `{scenario_dir}`",
        f"- Profile filter: `{profile_filter}`",
        f"- Scenario count: `{len(metrics)}`",
        "",
        "| Scenario | Profile | Throughput (tokens/s) | p50 (ms) | p95 (ms) | Peak Memory (MB) | Deterministic |",
        "|---|---|---:|---:|---:|---:|---|",
    ]

    for metric in metrics:
        lines.append(
            "| "
            f"{metric['scenario']} | {metric['_meta']['profile']} | {metric['throughput_tokens_per_sec']} | {metric['latency_ms_p50']} | "
            f"{metric['latency_ms_p95']} | {metric['peak_memory_mb']} | {metric['deterministic']} |"
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_hotspot_report(
    *,
    hotspots: list[dict[str, Any]],
    report_path: Path,
    run_id: str,
) -> None:
    lines = [
        "# A4 Hotspot Profile",
        "",
        f"- Run ID: `{run_id}`",
        f"- Timestamp (UTC): `{_utc_now()}`",
        f"- Profile source: `cProfile` self-time ranking",
        f"- Functions listed: `{len(hotspots)}`",
        "",
        "| Rank | Function | Location | Self Time (s) | Wall-Time Share (%) |",
        "|---:|---|---|---:|---:|",
    ]

    for idx, row in enumerate(hotspots, start=1):
        lines.append(
            f"| {idx} | {row['function']} | {row['location']} | {row['self_time_s']} | {row['wall_time_share_pct']} |"
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    default_artifact_root = V0_ROOT / "proofs" / "artifacts" / "2026-02-24_program_maximal" / "A4"
    parser = argparse.ArgumentParser(description="Run A4 conformance benchmark scenarios and emit metrics.")
    parser.add_argument(
        "--scenario-dir",
        type=Path,
        default=SCRIPT_PATH.parent / "scenarios",
        help="Directory containing scenario JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_artifact_root / "metrics",
        help="Metrics output directory.",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=default_artifact_root,
        help="Artifact root where benchmark/hotspot reports are written.",
    )
    parser.add_argument("--run-id", default=_default_run_id(), help="Run ID to stamp on emitted metrics.")
    parser.add_argument(
        "--profile-top",
        type=int,
        default=10,
        help="Number of hotspot rows to include in HOTSPOT_PROFILE.md (minimum 5).",
    )
    parser.add_argument(
        "--profile",
        choices=("all",) + ALLOWED_PROFILES,
        default="all",
        help="Benchmark profile selection. Use 'all' for full protocol runs.",
    )
    parser.add_argument(
        "--scenario-limit",
        type=int,
        default=0,
        help="Optional cap on selected scenarios (0 = no cap). Use only for prep smoke checks.",
    )
    parser.add_argument(
        "--telemetry-out",
        type=Path,
        default=default_artifact_root / "telemetry" / "progressive_events.jsonl",
        help="Path for progressive telemetry event mirror (JSONL).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    configure_env()
    run_id = str(args.run_id)

    scenarios = _load_scenarios(args.scenario_dir)
    selected_scenarios = _select_scenarios(
        scenarios,
        profile=str(args.profile),
        scenario_limit=max(0, int(args.scenario_limit)),
    )
    git_commit = _git_commit()
    experiment, comet_notes, remote_enabled = _make_comet_experiment(run_id=run_id)
    telemetry = ProgressiveTelemetry(
        run_id=run_id,
        output_path=args.telemetry_out,
        experiment=experiment,
    )
    telemetry.emit(
        event_type="run_start",
        phase="bootstrap",
        protocol_version=PROTOCOL_VERSION,
        git_commit=git_commit,
        profile_filter=str(args.profile),
        scenario_limit=max(0, int(args.scenario_limit)),
        scenario_count_total=len(scenarios),
        scenario_count_selected=len(selected_scenarios),
        remote_comet_enabled=remote_enabled,
        notes=comet_notes,
    )

    metrics: list[dict[str, Any]] = []
    for scenario in selected_scenarios:
        telemetry.emit(
            event_type="phase_milestone",
            phase="scenario_start",
            scenario=scenario.scenario,
            profile=scenario.profile,
            category=scenario.category,
            kind=scenario.kind,
            iterations=scenario.iterations,
            warmup_iterations=scenario.warmup_iterations,
        )
        metric = _run_scenario(
            scenario,
            run_id=run_id,
            git_commit=git_commit,
            code_root=CODE_ROOT,
            telemetry=telemetry,
        )
        metrics.append(metric)
        telemetry.emit(
            event_type="phase_milestone",
            phase="scenario_complete",
            scenario=scenario.scenario,
            profile=scenario.profile,
            throughput_tokens_per_sec=metric["throughput_tokens_per_sec"],
            latency_ms_p50=metric["latency_ms_p50"],
            latency_ms_p95=metric["latency_ms_p95"],
            peak_memory_mb=metric["peak_memory_mb"],
            deterministic=metric["deterministic"],
        )

    _write_metric_files(metrics, args.output_dir)
    telemetry.emit(
        event_type="phase_milestone",
        phase="metrics_written",
        metrics_dir=str(args.output_dir),
        metric_file_count=len(metrics),
    )

    hotspots = _run_profile(selected_scenarios, code_root=CODE_ROOT, top_n=int(args.profile_top))
    telemetry.emit(
        event_type="phase_milestone",
        phase="profiling_complete",
        hotspot_row_count=len(hotspots),
    )

    benchmark_report_path = args.artifact_root / "BENCHMARK_REPORT.md"
    hotspot_report_path = args.artifact_root / "HOTSPOT_PROFILE.md"

    _write_benchmark_report(
        metrics=metrics,
        report_path=benchmark_report_path,
        run_id=run_id,
        git_commit=git_commit,
        scenario_dir=args.scenario_dir,
        profile_filter=str(args.profile),
        protocol_version=PROTOCOL_VERSION,
    )
    _write_hotspot_report(
        hotspots=hotspots,
        report_path=hotspot_report_path,
        run_id=run_id,
    )
    telemetry.emit(
        event_type="phase_milestone",
        phase="reports_written",
        benchmark_report=str(benchmark_report_path),
        hotspot_report=str(hotspot_report_path),
    )

    summary = {
        "run_id": run_id,
        "protocol_version": PROTOCOL_VERSION,
        "profile_filter": str(args.profile),
        "scenario_limit": max(0, int(args.scenario_limit)),
        "scenario_count_selected": len(selected_scenarios),
        "remote_comet_enabled": remote_enabled,
        "comet_notes": comet_notes,
        "git_commit": git_commit,
        "scenario_count": len(metrics),
        "metrics_dir": str(args.output_dir),
        "benchmark_report": str(benchmark_report_path),
        "hotspot_report": str(hotspot_report_path),
        "telemetry_event_log": str(args.telemetry_out),
    }
    telemetry.emit(
        event_type="run_complete",
        phase="complete",
        status="PASS",
        summary=summary,
    )

    if experiment is not None:
        try:
            experiment.log_parameter("ws3_protocol_version", PROTOCOL_VERSION)
            experiment.log_parameter("ws3_profile_filter", str(args.profile))
            experiment.log_parameter("ws3_scenario_count_selected", len(selected_scenarios))
            experiment.log_parameter("ws3_scenario_limit", max(0, int(args.scenario_limit)))
            experiment.log_text("\n".join(comet_notes))
            experiment.end()
        except Exception:
            pass

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

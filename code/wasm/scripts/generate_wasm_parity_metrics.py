#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import resource
import subprocess
import time
from pathlib import Path

SCENARIOS = [
    "hello world",
    "line1\nline2",
    "ASCII symbols !@#$%^&*()[]{}",
    "Cafe\u0301",
    "naive facade cooperate",
    "emoji 🙂🚀🔥",
    "math alpha beta gamma",
    "tabs\tand spaces",
    "mixed accents: deja vu",
    "quotes 'single' and \"double\"",
]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(ordered[low])
    weight = rank - low
    return float(ordered[low] * (1.0 - weight) + ordered[high] * weight)


def git_commit(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def maxrss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes, Linux reports KB.
    if usage > 10_000_000:
        return round(usage / (1024.0 * 1024.0), 6)
    return round(usage / 1024.0, 6)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate wasm parity metrics JSON")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    wasm_dir = script_path.parents[1]
    code_root = wasm_dir.parent
    repo_root = code_root.parents[1]

    payload = json.dumps({"scenarios": SCENARIOS})

    start = time.perf_counter()
    result = subprocess.run(
        ["node", str(wasm_dir / "scripts" / "run_contract.mjs")],
        cwd=wasm_dir,
        input=payload,
        check=True,
        capture_output=True,
        text=True,
    )
    elapsed = max(time.perf_counter() - start, 1e-9)

    output_line = result.stdout.strip().splitlines()[-1]
    contract = json.loads(output_line)

    scenario_results = contract.get("results", [])
    latencies = [float(item["encode_ms"]) + float(item["decode_ms"]) for item in scenario_results]
    total_tokens = int(sum(int(item["token_count"]) for item in scenario_results))
    mismatch_count = int(contract.get("mismatch_count", 0))

    timestamp_utc = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = f"a5-wasm-parity-{timestamp_utc.replace(':', '').replace('-', '')}"

    metrics = {
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "git_commit": git_commit(repo_root),
        "scenario": "wasm_interface_contract_10_scenarios",
        "dataset_or_fixture": "inline_text_scenarios_v1",
        "throughput_tokens_per_sec": round(total_tokens / elapsed, 6),
        "latency_ms_p50": round(percentile(latencies, 0.50), 6),
        "latency_ms_p95": round(percentile(latencies, 0.95), 6),
        "peak_memory_mb": maxrss_mb(),
        "deterministic": mismatch_count == 0,
        "notes": "Parity measured via wasm/scripts/run_contract.mjs with async wrapper init.",
        "scenario_count": len(scenario_results),
        "mismatch_count": mismatch_count,
        "module_version": contract.get("module_version"),
        "total_tokens": total_tokens,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

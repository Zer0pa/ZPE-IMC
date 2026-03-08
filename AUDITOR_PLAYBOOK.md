# Auditor Playbook

This page is the shortest honest public audit path for ZPE-IMC Wave-1.

It is not a legal opinion, a scientific novelty ruling, or a substitute
for broader diligence. It is the shortest path to verify what the public
repo currently proves.

## Three Dimensions

- Dimension 1: integrated modality transport is real on the accepted IMC path.
- Dimension 2: the Rust-backed runtime is real and is the current operator path.
- Dimension 3: provenance/custody discipline explains which artifacts are current truth versus history.

## Shortest Public Audit Path

1. Acquire the current public snapshot:

```bash
git clone https://github.com/Zer0pa/ZPE-IMC.git zpe-imc
cd zpe-imc
```

2. Build the local environment and native kernel:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "./code[full,bench,dev]"
./code/rust/imc_kernel/build_install.sh
```

The editable install exposes the canonical `zpe_multimodal.*` package surface
used by the live public pytest path.

3. Verify backend truth:

```bash
python - <<'PY'
from zpe_multimodal.core.imc import get_kernel_backend_info
print(get_kernel_backend_info())
PY
```

Expected current backend facts:
- `backend='rust'`
- `compiled_extension=True`
- `fallback_used=False`

4. Run the local-only wrapper:

```bash
python ./executable/run_with_comet.py
```

For the public audit path, treat this as a local evidence run. `COMET_API_KEY`
and `OPIK_API_KEY` are not required.

Optional direct public pytest replay after the editable install:

```bash
python -m pytest code -q
```

Expected public snapshot truth:
- `169 passed, 1 skipped`
- the intentional skip is the operator-only A6 Triton byte-identity check

Output hygiene note:
- the default rerun writes a stamped local bundle under `proofs/reruns/IMC-Canonical-<UTC timestamp>/`
- shipped reference artifacts in `proofs/logs/` and `code/benchmarks/artifacts/` remain stable operator reference artifacts and are not overwritten by the default public/local rerun

Public Triton note:
- the shipped Triton ONNX model is validated against the committed public integrity manifest at `code/deployment/triton/model_repository/zpe_tokenizer_onnx/1/model.integrity.json`
- the byte-for-byte comparison against the A6 proof export is operator/private only and is not required for the public audit path

5. Inspect the rerun bundle you just created:
- `proofs/reruns/IMC-Canonical-<UTC timestamp>/phase6_run_of_record_manifest.json`
- `proofs/reruns/IMC-Canonical-<UTC timestamp>/phase6_comet_run.txt`
- `proofs/reruns/IMC-Canonical-<UTC timestamp>/benchmarks/BENCHMARK_REPORT.md`

Reference/operator artifacts remain available separately:
- `proofs/logs/phase6_run_of_record_manifest.json`
- `proofs/logs/phase6_comet_run.txt`
- `code/benchmarks/artifacts/BENCHMARK_REPORT.md`

## Authority Matrix

| Anchor / artifact | Class | What it is for | What it is not for |
|---|---|---|---|
| `780` historical split note | historical anchor | chronology only | current runtime verdict |
| `844` Wave-1 demo / `wave1.0` mixed-stream anchor | compatibility anchor | downstream compatibility and historical demo custody | current operator truth |
| `docs/family/IMC_COMPATIBILITY_VECTOR.json` SHA256 `9c8b905f6c1d30d057955aa9adf0f7ff9139853494dca673e5fbe69f24fba10e` | compatibility anchor | family pinning and downstream coordination | current saturated run identity |
| `IMC-Canonical-20260307T131330Z` | current operator truth | accepted March 7 run-of-record identity | historical-only context |
| `A4-BENCH-20260307T131414Z` | current operator truth | accepted benchmark identity | generic marketing claim |
| `backend=rust`, `compiled_extension=1`, `fallback_used=0` | current operator truth | runtime-path verification | optional preference |
| `170 passed` in a full operator tree | current operator truth | accepted full-lane verdict when the private A6 Triton export is present | compatibility contract |
| `169 passed, 1 skipped` in the public snapshot | current public audit truth | honest public rerun verdict when the operator-only A6 Triton check is intentionally skipped | full private/operator lane |
| `canonical_total_words_per_sec=276798.7185` | current operator truth | accepted throughput ceiling in `imc_stream_words/sec` | natural-language words/sec or generic media-codec supremacy |

If you only remember one rule: `844` is frozen compatibility truth and historical demo context; the March 7 run/log pair is current operator truth.

## Feature Flags And Keys

Manual feature-flag export is not required for the recommended public audit path above.

Why:
- `executable/run_with_comet.py` sets:
  - `STROKEGRAM_ENABLE_DIAGRAM=1`
  - `STROKEGRAM_ENABLE_MUSIC=1`
  - `STROKEGRAM_ENABLE_VOICE=1`
- helper/demo paths such as `build_canonical_demo_stream(require_env=False)` are explicitly written to avoid requiring manual flag export

Where flags still matter:
- raw `IMCEncoder()` construction defaults to `require_env=True`
- if you are doing ad hoc full-modality local probes outside the playbook, export the three `STROKEGRAM_ENABLE_*` flags above or use an explicitly documented `require_env=False` helper path

Manual API keys are also not required for the public audit path:
- local-only execution works without `COMET_API_KEY`
- local-only execution works without `OPIK_API_KEY`

## Expected Current Truth

Current operator truth is the later March 7 accepted run:
- `run_name=IMC-Canonical-20260307T131330Z`
- `benchmark_run_id=A4-BENCH-20260307T131414Z`
- `tests_passed=170`
- `tests_skipped=0`
- `tests_total=170`
- `canonical_total_words_per_sec=276798.7185`
- `throughput_encode_words_per_sec=94104.7837`
- `throughput_decode_words_per_sec=296145.6735`

Current public audit truth in the public snapshot is the local rerun bundle:
- `tests_passed=169`
- `tests_skipped=1`
- `tests_total=170`
- the intentional skip is `code/tests/test_triton_repo_layout_operator.py::test_triton_tokenizer_model_matches_private_a6_export_artifact`
- the skipped operator-only test depends on `proofs/artifacts/2026-02-24_program_maximal/A6/exported/zpe_tokenizer_op.onnx`, which is intentionally excluded from the public snapshot

All throughput numbers are `imc_stream_words/sec`, not natural-language words/sec.

## If Your Replay Disagrees

Treat it as a replay mismatch, not as a free-form argument. Capture:
- commit hash or acquired snapshot identity
- full `get_kernel_backend_info()` output
- exact command run
- stdout/stderr
- the relevant diff against:
  - your local rerun bundle under `proofs/reruns/IMC-Canonical-<UTC timestamp>/`
  - `proofs/logs/phase6_run_of_record_manifest.json`
  - `proofs/logs/phase6_comet_run.txt`

Then read:
- `PUBLIC_AUDIT_LIMITS.md`
- `docs/FAQ.md`
- `docs/ARCHITECTURE.md`

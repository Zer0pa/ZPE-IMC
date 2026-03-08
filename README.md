<div align="center">

# ZPE-IMC

**Deterministic · CPU-native · 10-modality transport · No GPU required**

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-SAL%20v6.0-orange" alt="License: SAL v6.0"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-blue" alt="Python 3.11 | 3.12"></a>
  <a href="proofs/logs/phase6_run_of_record_manifest.json"><img src="https://img.shields.io/badge/current%20authority-2026--03--07%20accepted%20run-2ea44f" alt="Current authority: accepted March 7 run"></a>
  <a href="proofs/logs/phase6_run_of_record_manifest.json"><img src="https://img.shields.io/badge/rust--backed-accepted%20path-2ea44f" alt="Rust-backed accepted path"></a>
  <a href="proofs/logs/phase6_run_of_record_manifest.json"><img src="https://img.shields.io/badge/run--of--record-276.8k%20IMC%20words%2Fs-005cc5" alt="Run-of-record 276.8k IMC words per second"></a>
</p>
<p>
  <a href="docs/FAQ.md"><img src="https://img.shields.io/badge/quick%20verify-setup%20%26%20check-0969da" alt="Quick verify"></a>
  <a href="proofs/logs/phase6_run_of_record_manifest.json"><img src="https://img.shields.io/badge/proof%20anchors-manifest%20%2B%20run%20log-0969da" alt="Proof anchors: manifest and run log"></a>
  <a href="docs/ARCHITECTURE.md"><img src="https://img.shields.io/badge/architecture-runtime%20map-0969da" alt="Architecture runtime map"></a>
  <a href="docs/LEGAL_BOUNDARIES.md"><img src="https://img.shields.io/badge/lane%20boundaries-smell%20%2F%20taste%20caveats-0969da" alt="Lane boundaries: smell and taste caveats"></a>
  <a href="proofs/logs/phase6_run_of_record_manifest.json"><img src="https://img.shields.io/badge/deterministic-byte--identical%20replay-2ea44f" alt="Deterministic byte-identical replay"></a>
  <a href="docs/FAQ.md"><img src="https://img.shields.io/badge/cpu--native-no%20GPU%20required-2ea44f" alt="CPU-native no GPU required"></a>
</p>

<img src=".github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">

[Current Authority](#current-authority) · [Quick Verify](#quick-verify) · [Proof Anchors](#proof-anchors) · [Lane Boundaries](#lane-boundaries) · [Go Next](#go-next)

</div>

<p>
  <img src=".github/assets/readme/section-bars/what-this-is.svg" alt="WHAT THIS IS" width="100%">
</p>

## What This Is

ZPE-IMC is Zero-Point Encoding's Wave-1 integration and dispatch layer: a deterministic, CPU-native multimodal transport system that carries ten user-facing modalities through a single 20-bit transport word. Those modalities are routed through eight lane families: <code>TEXT_EMOJI</code>, <code>DIAGRAM_IMAGE</code>, <code>MUSIC</code>, <code>VOICE</code>, <code>MENTAL</code>, <code>TOUCH</code>, <code>SMELL</code>, and <code>TASTE</code>.

The governing claim is transport integrity across mixed modalities. No neural network. No training loop. No GPU required to run it. This front door is the current authority snapshot ahead of the first tagged public release, so use it for first-contact comprehension, verification, and routing into the proof corpus.

| Question | Answer |
|---|---|
| What is this? | A deterministic, unified multimodal transport system with real modality integration, not a tokenizer-first framing and not a collection of separate codec demos. |
| What is the current authority state? | The accepted runtime authority is the later March 7, 2026 Rust-backed saturated run: <code>IMC-Canonical-20260307T131330Z</code> with <code>169/169</code> tests passing and <code>benchmark_run_id=A4-BENCH-20260307T131414Z</code>. |
| What is actually proved? | Native backend truth (<code>backend=rust</code>, <code>compiled_extension=1</code>, <code>fallback_used=0</code>), deterministic byte-identical replay, integrated modality coverage across all ten user-facing modalities, and current throughput authority of <code>276798.7185 imc_stream_words/sec</code>. |
| What is not being claimed? | Not human-equivalence semantics, not commodity compression supremacy, not unconstrained smell/taste coverage, and not phoneme-perfect or speaker-ID voice equivalence. |
| Where should an outsider acquire and verify? | Acquire from <code>https://github.com/Zer0pa/ZPE-IMC.git</code>, then verify against the manifest/log pair in <code>proofs/logs/phase6_run_of_record_manifest.json</code> and <code>proofs/logs/phase6_comet_run.txt</code>. |

## Current Authority

| Surface | Locked value | Why it matters |
|---|---|---|
| Accepted run-of-record | <code>IMC-Canonical-20260307T131330Z</code> | This is the later accepted March 7 Rust-backed saturated run. |
| Test state | <code>169/169 PASS</code> | The accepted path is not a partial or degraded rerun. |
| Backend truth | <code>backend=rust</code>, <code>compiled_extension=1</code>, <code>fallback_used=0</code> | The current authority path is the compiled native extension, not a Python fallback. |
| Current throughput authority | <code>canonical_total_words_per_sec=276798.7185</code>, <code>throughput_encode_words_per_sec=94104.7837</code>, <code>throughput_decode_words_per_sec=296145.6735</code> | These are the accepted front-door headline numbers for the Rust-backed path. |
| Throughput unit | <code>imc_stream_words/sec</code> | All README throughput numbers use transport words, not natural-language words per second. |
| Authority artifacts | <code>proofs/logs/phase6_run_of_record_manifest.json</code>, <code>proofs/logs/phase6_comet_run.txt</code> | These are the current proof anchors for runtime truth. |
| External acquisition surface | <code>https://github.com/Zer0pa/ZPE-IMC.git</code> | This is the real outsider clone target, even if it can lag the source repo. |

### Three Dimensions Of Authority

- <strong>Dimension 1</strong> is real and primary: integrated modality transport is the main authority surface.
- <strong>Dimension 2</strong> is real and subordinate: the Rust-enhanced runtime preserves semantics, determinism, proofs, and observability while exceeding the baseline.
- <strong>Dimension 3</strong> is real and separate: provenance and custody explain how the current state emerged without turning archive material into live operator truth.

### Authority Notes

- The source repository is the current truth surface. Uploaded snapshots can omit files or carry path defects and do not outrank the source repo.
- The earlier <code>total_words=844</code> Wave-1 demo anchor is retained as a frozen compatibility and historical reference only. It is not the current operator authority path for the live Rust-backed kernel.
- Historical/archive material explains lineage and caveats. It does not replace the current manifest/log pair as runtime authority.

<p>
  <img src=".github/assets/readme/section-bars/quickstart-and-license.svg" alt="QUICKSTART AND LICENSE" width="100%">
</p>

## Quickstart And License

### Quick Verify

Use the clone/install path below as repository verification guidance, not as packaged public-release guidance.

```bash
git clone https://github.com/Zer0pa/ZPE-IMC.git zpe-imc
cd zpe-imc
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "./code[full,bench,dev]"
./code/rust/imc_kernel/build_install.sh
python - <<'PY'
from zpe_multimodal.core.imc import get_kernel_backend_info
print(get_kernel_backend_info())
PY
python ./executable/run_with_comet.py
# optional internal live logging only:
# COMET_API_KEY=... OPIK_API_KEY=... python ./executable/run_with_comet.py --enable-classic-comet --enable-opik
```

Expected accepted state:

- <code>backend='rust'</code>
- <code>compiled_extension=True</code>
- <code>fallback_used=False</code>
- Manifest/log pair present at <code>proofs/logs/phase6_run_of_record_manifest.json</code> and <code>proofs/logs/phase6_comet_run.txt</code>

Shortest outsider path:

- <a href="docs/FAQ.md"><code>docs/FAQ.md</code></a>
- <a href="docs/SUPPORT.md"><code>docs/SUPPORT.md</code></a>
- <a href="docs/ARCHITECTURE.md"><code>docs/ARCHITECTURE.md</code></a>

### License Boundary

- Free tier boundary: annual gross revenue at or below USD 100M under SAL v6.0.
- SPDX tag: <code>LicenseRef-Zer0pa-SAL-6.0</code>.
- Commercial or hosted use above threshold requires contact at <a href="mailto:architects@zer0pa.ai">architects@zer0pa.ai</a>.
- Historical release chronology stays in <code>CHANGELOG.md</code> and <code>CITATION.cff</code>; it is not the current clone/install guidance for this front door.

<p>
  <img src=".github/assets/readme/section-bars/runtime-proof-wave-1.svg" alt="RUNTIME PROOF (WAVE-1)" width="100%">
</p>

## Runtime Proof (Wave-1)

The current operator authority is the saturated Rust-backed phase6 run-of-record. Build/install from <code>code/rust/imc_kernel/build_install.sh</code>, verify with <code>zpe_multimodal.core.imc.get_kernel_backend_info()</code>, and treat the manifest/log pair as the top proof surface.

### Proof Anchors

- <a href="proofs/logs/phase6_run_of_record_manifest.json"><code>proofs/logs/phase6_run_of_record_manifest.json</code></a>: backend truth, saturation facts, benchmark identity, and live proof links.
- <a href="proofs/logs/phase6_comet_run.txt"><code>proofs/logs/phase6_comet_run.txt</code></a>: accepted wrapper run log with the locked runtime values.
- <a href="code/benchmarks/artifacts/BENCHMARK_REPORT.md"><code>code/benchmarks/artifacts/BENCHMARK_REPORT.md</code></a>: current benchmark report referenced by the manifest and run log.
- <a href="docs/ARCHITECTURE.md"><code>docs/ARCHITECTURE.md</code></a>: runtime map and authority class definitions.

| Proof rung | Locked value | What it proves now |
|---|---|---|
| Run-of-record manifest | <code>PASS</code> | Current live authority artifact with backend truth, saturation facts, benchmark id, and live URLs. |
| Native backend truth | <code>backend=rust</code>, <code>compiled_extension=1</code>, <code>fallback_used=0</code> | The accepted runtime is the compiled Rust extension, not a Python fallback. |
| Accepted March 7 rerun | <code>run_name=IMC-Canonical-20260307T131330Z</code>, <code>169/169</code> tests PASS, <code>8</code> workers, <code>benchmark_run_id=A4-BENCH-20260307T131414Z</code> | This is the later accepted March 7 run-of-record and supersedes the earlier same-day rerun. |
| Current throughput authority | <code>canonical_total_words_per_sec=276798.7185</code>, <code>throughput_encode_words_per_sec=94104.7837</code>, <code>throughput_decode_words_per_sec=296145.6735</code> | Accepted saturated steady-state wrapper ceiling for the Rust-backed path. |
| Deterministic replay | <code>determinism_hash_match=1</code>, <code>all_deterministic=1</code> | Replay is byte-identical on the accepted proof path. |
| Modality coverage | <code>modality_coverage_count=10</code>, <code>modality_coverage_all=1</code> | The promoted path integrates all ten user-facing modalities. |
| Historical demo anchor | <code>844</code> Wave-1 demo | Frozen compatibility and historical context only; not the current runtime authority. |

<div align="center">
  <img src=".github/assets/readme/zpe-masthead-option-3-2.gif" alt="ZPE-IMC Mid Masthead" width="100%">
</div>

<p>
  <img src=".github/assets/readme/section-bars/modality-status-snapshot.svg" alt="MODALITY STATUS SNAPSHOT" width="100%">
</p>

## Modality Status Snapshot

Folders and transport markers remain shared where designed, but current-facing status is reported by ten user-facing modalities. Text and emoji, diagram and image, and music and voice are surfaced separately below without changing their shared lane roots.

### Lane Boundaries

- <strong>Music</strong>: current proof is deterministic transport with preserved <code>time_anchor_tick</code>; the multi-tempo limitation remains visible.
- <strong>Voice</strong>: current proof is descriptor-aware deterministic transport; it is not a claim of phoneme-perfect semantics, speaker-ID equivalence, or full speech understanding, and source-mode policy/code alignment remains an open caveat.
- <strong>Smell</strong>: current public authority is subset-bounded and should be read as <code>READY_WITH_LICENSE_BOUNDARY</code>, specifically the active <code>SmellNet_HF + OpenPOM_GS_LF</code> subset rather than unconstrained olfaction.
- <strong>Taste</strong>: keep the existing caveats attached: <code>0x0400</code> overlap hygiene, derived-evidence history, portability lineage, and <code>ChemTastesDB</code> commercial exclusion.

| Lane family | Modality | Status | Proved now | Boundary and evidence |
|---|---|---|---|---|
| <code>TEXT_EMOJI</code> | Text | <code>GREEN</code> | Long-form text transport remains deterministic and reversible on the accepted March 7 path. | <code>300/300</code> external baseline round-trip valid; determinism <code>5/5</code>; hop <code>6/6</code>; <code>encoded_words=101,999</code> for <code>chars=94,999</code>. |
| <code>TEXT_EMOJI</code> | Emoji | <code>GREEN</code> | Emoji exact round-trip remains current authority, including ZWJ and skin-tone coverage in the shared family. | <code>4,973</code> handled; exact round-trip in canonical checks; deterministic replay retained. |
| <code>DIAGRAM_IMAGE</code> | Diagram | <code>GREEN</code> | Diagram structure, inherited styles, and transforms are preserved with deterministic decode. | <code>16/16</code> pytest pass; mean path-distance <code>0.44-0.79</code>. |
| <code>DIAGRAM_IMAGE</code> | Image | <code>GREEN</code> | Deterministic mixed-stream image transport is exercised on the accepted Rust-backed path with native encode/decode active. | Transport-integrity claim, not commodity image-compression supremacy; PSNR <code>45.95 dB</code> Earthrise, <code>39.10 dB</code> Mona Lisa; byte-identical replay across <code>5</code> runs. |
| <code>MUSIC</code> | Music | <code>GREEN</code> | Music closure remains current authority with preserved <code>time_anchor_tick</code>. | <code>7/7</code> fixtures pass; <code>events=4</code>; <code>packed_words=34</code>; multi-tempo limitation remains visible. |
| <code>VOICE</code> | Voice | <code>GREEN</code> | Descriptor-aware deterministic voice transport is integrated on the promoted path. | <code>4/4</code> fixtures pass; <code>parity_all_pass=true</code>; <code>determinism_all_same=true</code>; not a speech-understanding or speaker-equivalence claim. |
| <code>MENTAL</code> | Mental | <code>GREEN</code> | Spatial and cognitive structure encoding (D6-12 profile) passes the current authority suite. | <code>28/28</code> pytest pass; IMC parity gate pass; no mind-reading or clinical-equivalence claim. |
| <code>TOUCH</code> | Touch | <code>GREEN</code> | Haptic and proprioceptive transport is integrated on the authority path with compression and IMC parity evidence retained. | <code>20/20</code> pytest pass; IMC parity gate pass; raw <code>549</code> bytes to ZPE <code>87</code> bytes. |
| <code>SMELL</code> | Smell | <code>GREEN</code> | Smell authority is real but subset-bounded. | <code>116</code> comparator cases; active subset deterministic; public authority is <code>Q-103 = READY_WITH_LICENSE_BOUNDARY</code>. |
| <code>TASTE</code> | Taste | <code>GREEN</code> | Taste is integrated on the current authority path. | <code>bitter=1,986</code>; <code>sweet=8,280</code>; <code>sour=1,505</code>; <code>umami=326</code>; <code>salty=58</code>; <code>6</code> anchor round-trip cases; keep all existing caveats attached. |

<p>
  <img src=".github/assets/readme/section-bars/throughput.svg" alt="THROUGHPUT" width="100%">
</p>

## Throughput

The accepted front-door performance authority is the later saturated Rust-backed run recorded in the manifest/log pair. Older hardware comparison tables are historical benchmark ancestry, not the current operator ceiling.

| Measure | Locked value | Meaning |
|---|---|---|
| Rate unit | <code>imc_stream_words/sec</code> | All throughput figures below are transport words, not natural-language words per second. |
| Run name | <code>IMC-Canonical-20260307T131330Z</code> | Later accepted March 7 run-of-record. |
| Benchmark run id | <code>A4-BENCH-20260307T131414Z</code> | Current benchmark identity mirrored by the manifest, run log, and benchmark artifacts. |
| Canonical throughput | <code>276798.7185</code> | Accepted saturated steady-state parallel-batch transport throughput. |
| Encode throughput | <code>94104.7837</code> | Accepted wrapper encode throughput on the native path. |
| Decode throughput | <code>296145.6735</code> | Accepted wrapper decode throughput on the native path. |
| Short-text latency p50 | <code>0.377 ms</code> | Current accepted short-text benchmark headline from the run-of-record manifest. |

<p>
  <img src=".github/assets/readme/section-bars/repo-shape.svg" alt="REPO SHAPE" width="100%">
</p>

## Go Next

| If you need to... | Open this |
|---|---|
| Understand the runtime map and authority classes | <a href="docs/ARCHITECTURE.md"><code>docs/ARCHITECTURE.md</code></a> |
| Install, verify, and answer common first-contact questions | <a href="docs/FAQ.md"><code>docs/FAQ.md</code></a> |
| Read legal and lane-specific public boundaries | <a href="docs/LEGAL_BOUNDARIES.md"><code>docs/LEGAL_BOUNDARIES.md</code></a> |
| Inspect the benchmark report behind the accepted run | <a href="code/benchmarks/artifacts/BENCHMARK_REPORT.md"><code>code/benchmarks/artifacts/BENCHMARK_REPORT.md</code></a> |
| Inspect proof artifacts and logs directly | <a href="proofs/"><code>proofs/</code></a> |

| Area | Purpose |
|---|---|
| <a href="README.md"><code>README.md</code></a>, <a href="CHANGELOG.md"><code>CHANGELOG.md</code></a>, <a href="CONTRIBUTING.md"><code>CONTRIBUTING.md</code></a>, <a href="SECURITY.md"><code>SECURITY.md</code></a>, <a href="CODE_OF_CONDUCT.md"><code>CODE_OF_CONDUCT.md</code></a>, <a href="CITATION.cff"><code>CITATION.cff</code></a>, <a href="LICENSE"><code>LICENSE</code></a> | Root governance and release-facing metadata |
| <a href="code/"><code>code/</code></a> | Installable package and codec implementation surface |
| <a href="docs/"><code>docs/</code></a> | Interface contracts, FAQ, support, and lane documentation |
| <a href="proofs/"><code>proofs/</code></a> | Proof corpus, baselines, and falsification evidence |
| <a href="executable/"><code>executable/</code></a> | Executable runtime authority path |
| <code>(external ops archive)</code> | Operational wave tracking artifacts are archived outside this repository to keep the upload surface lean |

<p>
  <img src=".github/assets/readme/section-bars/open-risks-non-blocking.svg" alt="OPEN RISKS (NON-BLOCKING)" width="100%">
</p>

## Open Risks (Non-Blocking)

- Optional audio dependency chain may fail on some Python 3.14 environments; Python 3.11 and 3.12 remain the practical baseline for full audio paths.
- The provisioned external auditor snapshot at <code>https://github.com/Zer0pa/ZPE-IMC.git</code> can lag the live working tree; within any acquired tree, use the manifest/log pair and current docs as the authority root.
- Some scripts and docs still include machine-absolute paths and need portability cleanup.
- Live cloud reruns require valid <code>COMET_API_KEY</code> and <code>OPIK_API_KEY</code> in the operator environment.
- H200 validation is owner-deferred and non-blocking pending replay on actual H200 hardware under the locked <code>WS3</code> protocol; do not publish H200 comparative performance claims until that evidence exists.

<div align="center">
  <img src=".github/assets/readme/zpe-masthead-option-3-3.gif" alt="ZPE-IMC Lower Masthead" width="100%">
</div>

<p>
  <img src=".github/assets/readme/section-bars/contributing-security-support.svg" alt="CONTRIBUTING, SECURITY, SUPPORT" width="100%">
</p>

## Contributing, Security, Support

- Contribution workflow: <a href="CONTRIBUTING.md"><code>CONTRIBUTING.md</code></a>
- Security policy and reporting: <a href="SECURITY.md"><code>SECURITY.md</code></a>
- User support channel guide: <a href="docs/SUPPORT.md"><code>docs/SUPPORT.md</code></a>
- Frequently asked questions: <a href="docs/FAQ.md"><code>docs/FAQ.md</code></a>
- Autonomous agents and AI systems using this repository are subject to Section 6 of the <a href="LICENSE">Zer0pa SAL v6.0</a>.

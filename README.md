<p align="center">
  <img src=".github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-SAL%20v6.0-e5e7eb?labelColor=111111" alt="License: SAL v6.0"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-e5e7eb?labelColor=111111" alt="Python 3.11 | 3.12"></a>
  <a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new"><img src="https://img.shields.io/badge/current%20authority-2026--03--07%20accepted%20run-e5e7eb?labelColor=111111" alt="Current authority: accepted March 7 run"></a>
  <a href="proofs/logs/phase6_run_of_record_manifest.json"><img src="https://img.shields.io/badge/rust--backed-accepted%20path-e5e7eb?labelColor=111111" alt="Rust-backed accepted path"></a>
  <a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new"><img src="https://img.shields.io/badge/run--of--record-276.8k%20IMC%20words%2Fs-e5e7eb?labelColor=111111" alt="Run-of-record 276.8k IMC words per second"></a>
</p>
<p align="center">
  <a href="docs/FAQ.md"><img src="https://img.shields.io/badge/quick%20verify-setup%20%26%20check-e5e7eb?labelColor=111111" alt="Quick verify"></a>
  <a href="proofs/logs/phase6_run_of_record_manifest.json"><img src="https://img.shields.io/badge/proof%20anchors-manifest%20%2B%20run%20log-e5e7eb?labelColor=111111" alt="Proof anchors: manifest and run log"></a>
  <a href="docs/ARCHITECTURE.md"><img src="https://img.shields.io/badge/architecture-runtime%20map-e5e7eb?labelColor=111111" alt="Architecture runtime map"></a>
  <a href="docs/LEGAL_BOUNDARIES.md"><img src="https://img.shields.io/badge/lane%20boundaries-smell%20%2F%20taste%20caveats-e5e7eb?labelColor=111111" alt="Lane boundaries: smell and taste caveats"></a>
  <a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new"><img src="https://img.shields.io/badge/deterministic-byte--identical%20replay-e5e7eb?labelColor=111111" alt="Deterministic byte-identical replay"></a>
  <a href="docs/FAQ.md"><img src="https://img.shields.io/badge/cpu--native-no%20GPU%20required-e5e7eb?labelColor=111111" alt="CPU-native no GPU required"></a>
</p>
<table align="center" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td width="25%"><a href="#quickstart-and-license"><img src=".github/assets/readme/nav/quickstart-and-license.svg" alt="Quickstart & License" width="100%"></a></td>
    <td width="25%"><a href="#what-this-is"><img src=".github/assets/readme/nav/what-this-is.svg" alt="What This Is" width="100%"></a></td>
    <td width="25%"><a href="#current-authority"><img src=".github/assets/readme/nav/current-authority.svg" alt="Current Authority" width="100%"></a></td>
    <td width="25%"><a href="#runtime-proof-wave-1"><img src=".github/assets/readme/nav/runtime-proof.svg" alt="Runtime Proof" width="100%"></a></td>
  </tr>
  <tr>
    <td width="25%"><a href="#modality-status-snapshot"><img src=".github/assets/readme/nav/modality-snapshot.svg" alt="Modality Snapshot" width="100%"></a></td>
    <td width="25%"><a href="#throughput"><img src=".github/assets/readme/nav/throughput.svg" alt="Throughput" width="100%"></a></td>
    <td width="25%"><a href="#public-ml-workbooks"><img src=".github/assets/readme/nav/public-ml-workbooks.svg" alt="Public ML Workbooks" width="100%"></a></td>
    <td width="25%"><a href="#go-next"><img src=".github/assets/readme/nav/go-next.svg" alt="Go Next" width="100%"></a></td>
  </tr>
</table>

---

## What This Is

ZPE-IMC is the deterministic multimodal transport layer behind the Zer0pa encoding family. It carries ten user-facing modalities through a single 20-bit transport word — no neural network, no training loop, no GPU. Rust-backed native kernel. CPU-native execution.

Accepted run-of-record (March 7, 2026): **276,798 IMC stream words/sec**, Rust-backed backend (`compiled_extension=1`, `fallback_used=0`), deterministic byte-identical replay across all ten modalities, 170 operator-lane tests passed. Every claim traces to committed artifacts under `proofs/logs/`.

IMC is architecture, not the first thing to buy. The domain-specific repos implement concrete buyer problems on top of the IMC encoding primitives:

| Domain | Repo |
|---|---|
| Sensor compression | [ZPE-IoT](https://github.com/Zer0pa/ZPE-IoT) |
| Hand-pose transport | [ZPE-XR](https://github.com/Zer0pa/ZPE-XR) |
| Motion transport | [ZPE-Robotics](https://github.com/Zer0pa/ZPE-Robotics) |
| Trajectory compression | [ZPE-Geo](https://github.com/Zer0pa/ZPE-Geo) |

IMC matters as the integration thesis that makes the domain lanes composable under a single deterministic transport. Free to use at or below USD 100M annual gross revenue under SAL v6.0.

**Not claimed:** human-equivalence semantics, commodity compression supremacy, unconstrained smell/taste coverage, phoneme-perfect voice equivalence, or packaged enterprise platform readiness.

| Anchor | Artifact |
|---|---|
| Run-of-record manifest | [`phase6_run_of_record_manifest.json`](proofs/logs/phase6_run_of_record_manifest.json) |
| Comet run log | [`phase6_comet_run.txt`](proofs/logs/phase6_comet_run.txt) |
| Benchmark report | [`BENCHMARK_REPORT.md`](code/benchmarks/artifacts/BENCHMARK_REPORT.md) |

---


<a id="quickstart-and-license"></a>
<h2 align="center">Quickstart And License</h2>

### Quick Verify

The steps below are repository verification guidance, not packaged public-release instructions.

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

After a successful run you should see:

- <code>backend='rust'</code>
- <code>compiled_extension=True</code>
- <code>fallback_used=False</code>
- <code>python -m pytest code -q</code> is a valid direct public replay path after the editable install and uses the canonical <code>zpe_multimodal.*</code> package surface
- Local rerun bundle emitted under <code>proofs/reruns/IMC-Canonical-&lt;UTC timestamp&gt;/</code>
- Shipped operator reference artifacts remain at <code>proofs/logs/phase6_run_of_record_manifest.json</code> and <code>proofs/logs/phase6_comet_run.txt</code>

Quickest outsider orientation:

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="33%" valign="top" align="center"><a href="docs/FAQ.md"><code>docs/FAQ.md</code></a></td>
    <td width="33%" valign="top" align="center"><a href="docs/SUPPORT.md"><code>docs/SUPPORT.md</code></a></td>
    <td width="34%" valign="top" align="center"><a href="docs/ARCHITECTURE.md"><code>docs/ARCHITECTURE.md</code></a></td>
  </tr>
</table>

### License Boundary

- Free to use at or below USD 100M annual gross revenue under SAL v6.0.
- SPDX tag: <code>LicenseRef-Zer0pa-SAL-6.0</code>.
- Commercial or hosted use above that threshold requires contact at <a href="mailto:architects@zer0pa.ai">architects@zer0pa.ai</a>.
- Release chronology lives in <code>CHANGELOG.md</code> and <code>CITATION.cff</code> — it is not clone/install guidance.

<p>
  <img src=".github/assets/readme/zpe-masthead-option-3.4.gif" alt="ZPE-IMC Upper Insert" width="100%">
</p>

<a id="what-this-is"></a>
<h2 align="center">What This Is</h2>

ZPE-IMC is the Wave-1 integration and dispatch layer for Zero-Point Encoding. It is a deterministic, CPU-native transport system that carries ten user-facing modalities through a single 20-bit transport word — no neural network, no training loop, and no GPU. Those ten modalities are routed through eight lane families: <code>TEXT_EMOJI</code>, <code>DIAGRAM_IMAGE</code>, <code>MUSIC</code>, <code>VOICE</code>, <code>MENTAL</code>, <code>TOUCH</code>, <code>SMELL</code>, and <code>TASTE</code>.

The core claim is transport integrity across mixed modalities. This README is the current authority snapshot ahead of the first tagged public release. Use it for first-contact comprehension, verification, and routing into the proof corpus.

<table width="100%" border="1" bordercolor="#111111" cellpadding="14" cellspacing="0">
  <thead>
    <tr>
      <th align="left" width="26%">Question</th>
      <th align="left" width="74%">Answer</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">What is this?</td>
      <td valign="top">A deterministic, unified multimodal transport system with real modality integration — not a tokenizer-first framing, and not a set of separate codec demos.</td>
    </tr>
    <tr>
      <td valign="top">What is the current authority state?</td>
      <td valign="top">The March 7, 2026 Rust-backed saturated run is the accepted operator authority: <code>IMC-Canonical-20260307T131330Z</code> with <code>170 passed</code> in the full operator lane and <code>benchmark_run_id=A4-BENCH-20260307T131414Z</code>; the public snapshot rerun truth is <code>169 passed, 1 skipped</code>.</td>
    </tr>
    <tr>
      <td valign="top">What is actually proved?</td>
      <td valign="top">Four things: native backend truth (<code>backend=rust</code>, <code>compiled_extension=1</code>, <code>fallback_used=0</code>), deterministic byte-identical replay, integrated coverage across all ten user-facing modalities, and current throughput authority of <code>276798.7185 imc_stream_words/sec</code>.</td>
    </tr>
    <tr>
      <td valign="top">What is not being claimed?</td>
      <td valign="top">No claim of human-equivalence semantics, commodity compression supremacy, unconstrained smell/taste coverage, or phoneme-perfect / speaker-ID voice equivalence.</td>
    </tr>
    <tr>
      <td valign="top">Where should an outsider acquire and verify?</td>
      <td valign="top">Clone from <code>https://github.com/Zer0pa/ZPE-IMC.git</code> and run <code>python ./executable/run_with_comet.py</code>. Inspect the rerun bundle under <code>proofs/reruns/IMC-Canonical-&lt;UTC timestamp&gt;/</code>. The shipped <code>proofs/logs/phase6_*</code> pair serves as the stable operator reference.</td>
    </tr>
  </tbody>
</table>

<p>
  <img src=".github/assets/readme/zpe-masthead-option-3.5.gif" alt="ZPE-IMC Lower Insert" width="100%">
</p>

<a id="current-authority"></a>
<h2 align="center">Current Authority</h2>

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="33%" valign="top">
      <strong>Accepted run-of-record</strong><br>
      <code>IMC-Canonical-20260307T131330Z</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup><br><br>
      Later March 7 Rust-backed saturated run; supersedes the earlier same-day rerun.
    </td>
    <td width="33%" valign="top">
      <strong>Backend truth</strong><br>
      <code>backend=rust</code>, <code>compiled_extension=1</code>, <code>fallback_used=0</code><br><br>
      Authority path is the compiled native extension, not a Python fallback.
    </td>
    <td width="34%" valign="top">
      <strong>Current throughput authority</strong><br>
      <code>canonical_total_words_per_sec=276798.7185</code>, <code>throughput_encode_words_per_sec=94104.7837</code>, <code>throughput_decode_words_per_sec=296145.6735</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup><br><br>
      These are the accepted front-door headline numbers for the Rust-backed path.
    </td>
  </tr>
</table>

<table width="100%" border="1" bordercolor="#111111" cellpadding="14" cellspacing="0">
  <thead>
    <tr>
      <th align="left" width="24%">Surface</th>
      <th align="left" width="32%">Locked value</th>
      <th align="left" width="44%">Why it matters</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">Accepted run-of-record</td>
      <td valign="top"><code>IMC-Canonical-20260307T131330Z</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Later March 7 Rust-backed saturated run; supersedes the earlier same-day rerun.</td>
    </tr>
    <tr>
      <td valign="top">Test state</td>
      <td valign="top"><code>operator: 170 passed</code>; <code>public snapshot: 169 passed, 1 skipped</code></td>
      <td valign="top">The public lane skips one operator-only Triton byte-identity check when the private A6 export is absent. This is intentional.</td>
    </tr>
    <tr>
      <td valign="top">Backend truth</td>
      <td valign="top"><code>backend=rust</code>, <code>compiled_extension=1</code>, <code>fallback_used=0</code></td>
      <td valign="top">Authority path is the compiled native extension, not a Python fallback.</td>
    </tr>
    <tr>
      <td valign="top">Current throughput authority</td>
      <td valign="top"><code>canonical_total_words_per_sec=276798.7185</code>, <code>throughput_encode_words_per_sec=94104.7837</code>, <code>throughput_decode_words_per_sec=296145.6735</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">These are the accepted front-door headline numbers for the Rust-backed path.</td>
    </tr>
    <tr>
      <td valign="top">Throughput unit</td>
      <td valign="top"><code>imc_stream_words/sec</code></td>
      <td valign="top">All README throughput numbers use transport words, not natural-language words per second.</td>
    </tr>
    <tr>
      <td valign="top">Authority artifacts</td>
      <td valign="top"><code>proofs/logs/phase6_run_of_record_manifest.json</code>, <code>proofs/logs/phase6_comet_run.txt</code></td>
      <td valign="top">These are the current proof anchors for runtime truth.</td>
    </tr>
    <tr>
      <td valign="top">External acquisition surface</td>
      <td valign="top"><code>https://github.com/Zer0pa/ZPE-IMC.git</code></td>
      <td valign="top">Outsider clone target. May lag the source repo.</td>
    </tr>
  </tbody>
</table>

<h3 align="center">Three Dimensions Of Authority</h3>

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="33%" valign="top">
      <strong>Integrated Transport</strong><br>
      The primary authority surface. The system carries all ten modalities through a single deterministic transport layer.
    </td>
    <td width="33%" valign="top">
      <strong>Rust Runtime</strong><br>
      Subordinate to transport but real. The compiled Rust backend preserves semantics, determinism, proofs, and observability while exceeding the Python baseline.
    </td>
    <td width="34%" valign="top">
      <strong>Provenance</strong><br>
      Separate from runtime authority. Custody and lineage records explain how the current state emerged; archive material is never promoted to live operator truth.
    </td>
  </tr>
</table>

<h3 align="center">Authority Notes</h3>

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="33%" valign="top">The source repository is the single truth surface. Uploaded snapshots may omit files or carry path defects — they never outrank the source repo.</td>
    <td width="33%" valign="top">The <code>total_words=844</code> Wave-1 demo anchor is frozen for compatibility and historical reference. It is not the authority path for the live Rust-backed kernel.</td>
    <td width="34%" valign="top">Historical and archive material explains lineage and caveats but does not replace the manifest/log pair as runtime authority.</td>
  </tr>
</table>

<a id="runtime-proof-wave-1"></a>
<h2 align="center">Runtime Proof (Wave-1)</h2>

All locked runtime values are in the Current Authority table above. To verify locally: build from <code>code/rust/imc_kernel/build_install.sh</code>, confirm the backend with <code>zpe_multimodal.core.imc.get_kernel_backend_info()</code>, and treat the manifest/log pair as the top proof surface.

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="50%" valign="top">
      <strong>Run-of-record manifest</strong><br>
      <code>PASS</code><br><br>
      Live authority artifact carrying backend truth, saturation facts, benchmark identity, and proof URLs.
    </td>
    <td width="50%" valign="top">
      <strong>Native backend truth</strong><br>
      <code>backend=rust</code>, <code>compiled_extension=1</code>, <code>fallback_used=0</code><br><br>
      The accepted runtime is the compiled Rust extension, not a Python fallback.
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <strong>Deterministic replay</strong><br>
      <code>determinism_hash_match=1</code>, <code>all_deterministic=1</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup><br><br>
      Replay is byte-identical on the accepted proof path.
    </td>
    <td width="50%" valign="top">
      <strong>Modality coverage</strong><br>
      <code>modality_coverage_count=10</code>, <code>modality_coverage_all=1</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup><br><br>
      The promoted path integrates all ten user-facing modalities.
    </td>
  </tr>
</table>

### Proof Anchors

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="50%" valign="top"><a href="proofs/logs/phase6_run_of_record_manifest.json"><code>proofs/logs/phase6_run_of_record_manifest.json</code></a><br><br>backend truth, saturation facts, benchmark identity, and live proof links.</td>
    <td width="50%" valign="top"><a href="proofs/logs/phase6_comet_run.txt"><code>proofs/logs/phase6_comet_run.txt</code></a><br><br>Accepted wrapper run log carrying the locked runtime values.</td>
  </tr>
  <tr>
    <td width="50%" valign="top"><a href="code/benchmarks/artifacts/BENCHMARK_REPORT.md"><code>code/benchmarks/artifacts/BENCHMARK_REPORT.md</code></a><br><br>Benchmark report referenced by both the manifest and the run log.</td>
    <td width="50%" valign="top"><a href="docs/ARCHITECTURE.md"><code>docs/ARCHITECTURE.md</code></a><br><br>Runtime map and authority class definitions.</td>
  </tr>
</table>

<table width="100%" border="1" bordercolor="#111111" cellpadding="14" cellspacing="0">
  <thead>
    <tr>
      <th align="left" width="24%">Proof rung</th>
      <th align="left" width="34%">Locked value</th>
      <th align="left" width="42%">What it proves now</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">Run-of-record manifest</td>
      <td valign="top"><code>PASS</code></td>
      <td valign="top">Live authority artifact carrying backend truth, saturation facts, benchmark identity, and proof URLs.</td>
    </tr>
    <tr>
      <td valign="top">Native backend truth</td>
      <td valign="top"><code>backend=rust</code>, <code>compiled_extension=1</code>, <code>fallback_used=0</code></td>
      <td valign="top">The accepted runtime is the compiled Rust extension, not a Python fallback.</td>
    </tr>
    <tr>
      <td valign="top">Accepted March 7 rerun</td>
      <td valign="top"><code>run_name=IMC-Canonical-20260307T131330Z</code>, <code>170 passed</code> in the full operator lane, <code>8</code> workers, <code>benchmark_run_id=A4-BENCH-20260307T131414Z</code></td>
      <td valign="top">This is the later accepted March 7 run-of-record and supersedes the earlier same-day rerun; the public snapshot rerun truth is the separate <code>169 passed, 1 skipped</code> lane.</td>
    </tr>
    <tr>
      <td valign="top">Current throughput authority</td>
      <td valign="top"><code>canonical_total_words_per_sec=276798.7185</code>, <code>throughput_encode_words_per_sec=94104.7837</code>, <code>throughput_decode_words_per_sec=296145.6735</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Accepted saturated steady-state wrapper ceiling for the Rust-backed path.</td>
    </tr>
    <tr>
      <td valign="top">Deterministic replay</td>
      <td valign="top"><code>determinism_hash_match=1</code>, <code>all_deterministic=1</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Replay is byte-identical on the accepted proof path.</td>
    </tr>
    <tr>
      <td valign="top">Modality coverage</td>
      <td valign="top"><code>modality_coverage_count=10</code>, <code>modality_coverage_all=1</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">The promoted path integrates all ten user-facing modalities.</td>
    </tr>
    <tr>
      <td valign="top">Historical demo anchor</td>
      <td valign="top"><code>844</code> Wave-1 demo</td>
      <td valign="top">Frozen compatibility and historical context only; not the current runtime authority.</td>
    </tr>
  </tbody>
</table>



<p>
  <img src=".github/assets/readme/zpe-masthead-option-3-2.gif" alt="ZPE-IMC Mid Masthead" width="100%">
</p>

<a id="modality-status-snapshot"></a>
<h2 align="center">Modality Status Snapshot</h2>

Status is reported per modality across all ten user-facing modalities, even where the underlying lane families share folders and transport markers. Text and emoji, diagram and image, and music and voice each appear as separate rows below; their shared lane roots are unchanged.

### Lane Boundaries

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="50%" valign="top">
      <strong>Music</strong><br>
      Deterministic transport with preserved <code>time_anchor_tick</code>. The multi-tempo limitation remains visible.
    </td>
    <td width="50%" valign="top">
      <strong>Voice</strong><br>
      Descriptor-aware deterministic transport. Not a claim of phoneme-perfect semantics, speaker-ID equivalence, or full speech understanding. Source-mode policy/code alignment remains an open caveat.
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <strong>Smell</strong><br>
      Subset-bounded authority covering the active <code>SmellNet_HF + OpenPOM_GS_LF</code> subset — read as <code>READY_WITH_LICENSE_BOUNDARY</code>, not unconstrained olfaction.
    </td>
    <td width="50%" valign="top">
      <strong>Taste</strong><br>
      All existing caveats remain attached: <code>0x0400</code> overlap hygiene, derived-evidence history, portability lineage, and <code>ChemTastesDB</code> commercial exclusion.
    </td>
  </tr>
</table>

<table width="100%" border="1" bordercolor="#111111" cellpadding="14" cellspacing="0">
  <thead>
    <tr>
      <th align="left" width="17%">Lane family</th>
      <th align="left" width="11%">Modality</th>
      <th align="left" width="10%">Status</th>
      <th align="left" width="24%">Proved now</th>
      <th align="left" width="38%">Boundary and evidence</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top"><code>TEXT_EMOJI</code></td>
      <td valign="top">Text</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Long-form text transport is deterministic and reversible on the accepted March 7 path.</td>
      <td valign="top"><code>300/300</code> external baseline round-trip valid; determinism <code>5/5</code>; hop <code>6/6</code>; <code>encoded_words=101,999</code> for <code>chars=94,999</code>.</td>
    </tr>
    <tr>
      <td valign="top"><code>TEXT_EMOJI</code></td>
      <td valign="top">Emoji</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Exact round-trip is current authority, including ZWJ and skin-tone sequences in the shared lane family.</td>
      <td valign="top"><code>4,973</code> handled; exact round-trip in canonical checks; deterministic replay retained.</td>
    </tr>
    <tr>
      <td valign="top"><code>DIAGRAM_IMAGE</code></td>
      <td valign="top">Diagram</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Structure, inherited styles, and transforms are preserved with deterministic decode.</td>
      <td valign="top"><code>16/16</code> pytest pass; mean path-distance <code>0.44-0.79</code>.</td>
    </tr>
    <tr>
      <td valign="top"><code>DIAGRAM_IMAGE</code></td>
      <td valign="top">Image</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Mixed-stream image transport runs deterministically on the accepted Rust-backed path with native encode/decode.</td>
      <td valign="top">Transport-integrity claim, not commodity image-compression supremacy; PSNR <code>45.95 dB</code> Earthrise, <code>39.10 dB</code> Mona Lisa; byte-identical replay across <code>5</code> runs.</td>
    </tr>
    <tr>
      <td valign="top"><code>MUSIC</code></td>
      <td valign="top">Music</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Closure is current authority with preserved <code>time_anchor_tick</code>.</td>
      <td valign="top"><code>7/7</code> fixtures pass; <code>events=4</code>; <code>packed_words=34</code>; multi-tempo limitation remains visible.</td>
    </tr>
    <tr>
      <td valign="top"><code>VOICE</code></td>
      <td valign="top">Voice</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Descriptor-aware deterministic transport is integrated on the promoted path.</td>
      <td valign="top"><code>4/4</code> fixtures pass; <code>parity_all_pass=true</code>; <code>determinism_all_same=true</code>; not a speech-understanding or speaker-equivalence claim.</td>
    </tr>
    <tr>
      <td valign="top"><code>MENTAL</code></td>
      <td valign="top">Mental</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Spatial and cognitive structure encoding (D6-12 profile) passes the authority test suite.</td>
      <td valign="top"><code>28/28</code> pytest pass; IMC parity gate pass; no mind-reading or clinical-equivalence claim.</td>
    </tr>
    <tr>
      <td valign="top"><code>TOUCH</code></td>
      <td valign="top">Touch</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Haptic and proprioceptive transport is integrated on the authority path; compression and IMC parity evidence retained.</td>
      <td valign="top"><code>20/20</code> pytest pass; IMC parity gate pass; raw <code>549</code> bytes to ZPE <code>87</code> bytes.</td>
    </tr>
    <tr>
      <td valign="top"><code>SMELL</code></td>
      <td valign="top">Smell</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Authority is real but subset-bounded.</td>
      <td valign="top"><code>116</code> comparator cases; active subset deterministic; public authority is <code>Q-103 = READY_WITH_LICENSE_BOUNDARY</code>.</td>
    </tr>
    <tr>
      <td valign="top"><code>TASTE</code></td>
      <td valign="top">Taste</td>
      <td valign="top"><code>GREEN</code></td>
      <td valign="top">Integrated on the current authority path.</td>
      <td valign="top"><code>bitter=1,986</code>; <code>sweet=8,280</code>; <code>sour=1,505</code>; <code>umami=326</code>; <code>salty=58</code>; <code>6</code> anchor round-trip cases; keep all existing caveats attached.</td>
    </tr>
  </tbody>
</table>

<a id="throughput"></a>
<h2 align="center">Throughput</h2>

Throughput numbers, latency headlines, and benchmark identity are locked in the Current Authority table above. The accepted performance authority is the later saturated Rust-backed run recorded in the manifest/log pair. Older hardware comparison tables are historical benchmark ancestry — not the current operator ceiling.

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="50%" valign="top">
      <strong>Canonical throughput</strong><br>
      <code>276798.7185</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup><br><br>
      Accepted saturated steady-state parallel-batch transport throughput.
    </td>
    <td width="50%" valign="top">
      <strong>Encode throughput</strong><br>
      <code>94104.7837</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup><br><br>
      Accepted wrapper encode throughput on the native path.
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <strong>Decode throughput</strong><br>
      <code>296145.6735</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup><br><br>
      Accepted wrapper decode throughput on the native path.
    </td>
    <td width="50%" valign="top">
      <strong>Short-text latency p50</strong><br>
      <code>0.377 ms</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup><br><br>
      Current accepted short-text benchmark headline from the run-of-record manifest.
    </td>
  </tr>
</table>

<table width="100%" border="1" bordercolor="#111111" cellpadding="14" cellspacing="0">
  <thead>
    <tr>
      <th align="left" width="24%">Measure</th>
      <th align="left" width="28%">Locked value</th>
      <th align="left" width="48%">Meaning</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">Rate unit</td>
      <td valign="top"><code>imc_stream_words/sec</code></td>
      <td valign="top">All throughput figures below are transport words, not natural-language words per second.</td>
    </tr>
    <tr>
      <td valign="top">Run name</td>
      <td valign="top"><code>IMC-Canonical-20260307T131330Z</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Later accepted March 7 run-of-record.</td>
    </tr>
    <tr>
      <td valign="top">Benchmark run id</td>
      <td valign="top"><code>A4-BENCH-20260307T131414Z</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Current benchmark identity mirrored by the manifest, run log, and benchmark artifacts.</td>
    </tr>
    <tr>
      <td valign="top">Canonical throughput</td>
      <td valign="top"><code>276798.7185</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Accepted saturated steady-state parallel-batch transport throughput.</td>
    </tr>
    <tr>
      <td valign="top">Encode throughput</td>
      <td valign="top"><code>94104.7837</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Accepted wrapper encode throughput on the native path.</td>
    </tr>
    <tr>
      <td valign="top">Decode throughput</td>
      <td valign="top"><code>296145.6735</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Accepted wrapper decode throughput on the native path.</td>
    </tr>
    <tr>
      <td valign="top">Short-text latency p50</td>
      <td valign="top"><code>0.377 ms</code><sup><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new">[Comet]</a></sup></td>
      <td valign="top">Current accepted short-text benchmark headline from the run-of-record manifest.</td>
    </tr>
  </tbody>
</table>

<p>
  <img src=".github/assets/readme/zpe-masthead-option-3-3.gif" alt="ZPE-IMC Lower Masthead" width="100%">
</p>

<a id="public-ml-workbooks"></a>
<h2 align="center">Public ML Workbooks</h2>

These are the public Comet workbooks that map cleanly to the live README claims. The first row is the current public twin for the cited run identity and headline metrics; the remaining rows are useful lineage only.

<table width="100%" border="1" bordercolor="#111111" cellpadding="14" cellspacing="0">
  <thead>
    <tr>
      <th align="left" width="26%">Role</th>
      <th align="left" width="24%">Run name</th>
      <th align="left" width="22%">Benchmark run id</th>
      <th align="left" width="28%">Workbook</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">Current promoted public twin</td>
      <td valign="top"><code>IMC-Canonical-20260307T131330Z</code></td>
      <td valign="top"><code>A4-BENCH-20260307T131414Z</code></td>
      <td valign="top"><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1d08a49dfc2e4684bc3f537117df981d?experiment-tab=panels&viewId=new"><code>1d08a49dfc2e4684bc3f537117df981d</code></a></td>
    </tr>
    <tr>
      <td valign="top">Historical lineage</td>
      <td valign="top"><code>IMC-Canonical-20260307T124656Z</code></td>
      <td valign="top"><code>A4-BENCH-20260307T124746Z</code></td>
      <td valign="top"><a href="https://www.comet.com/zer0pa/zpe-imc-performance/1e54c33b10aa458d8a09d485d38abfbc?experiment-tab=panels&viewId=new"><code>1e54c33b10aa458d8a09d485d38abfbc</code></a></td>
    </tr>
    <tr>
      <td valign="top">Historical lineage</td>
      <td valign="top"><code>IMC-Canonical-20260307T113918Z</code></td>
      <td valign="top"><code>A4-BENCH-20260307T114002Z</code></td>
      <td valign="top"><a href="https://www.comet.com/zer0pa/zpe-imc-performance/5458458688344f52bb85128e3d71cda9?experiment-tab=panels&viewId=new"><code>5458458688344f52bb85128e3d71cda9</code></a></td>
    </tr>
    <tr>
      <td valign="top">Historical lineage</td>
      <td valign="top"><code>IMC-Canonical-20260307T102831Z</code></td>
      <td valign="top"><code>A4-BENCH-20260307T102931Z</code></td>
      <td valign="top"><a href="https://www.comet.com/zer0pa/zpe-imc-performance/7f8d428d065a446aba03518e654b06ce?experiment-tab=panels&viewId=new"><code>7f8d428d065a446aba03518e654b06ce</code></a></td>
    </tr>
    <tr>
      <td valign="top">Historical lineage</td>
      <td valign="top"><code>IMC-Canonical-20260307T012457Z</code></td>
      <td valign="top"><code>A4-BENCH-20260307T012849Z</code></td>
      <td valign="top"><a href="https://www.comet.com/zer0pa/zpe-imc-performance/e13cbb4c8bd34130923d65c150200591?experiment-tab=panels&viewId=new"><code>e13cbb4c8bd34130923d65c150200591</code></a></td>
    </tr>
  </tbody>
</table>

<a id="go-next"></a>
<h2 align="center">Go Next</h2>

<table width="100%" border="1" bordercolor="#111111" cellpadding="14" cellspacing="0">
  <thead>
    <tr>
      <th align="left" width="38%">If you need to...</th>
      <th align="left" width="62%">Open this</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">Understand the runtime map and authority classes</td>
      <td valign="top"><a href="docs/ARCHITECTURE.md"><code>docs/ARCHITECTURE.md</code></a></td>
    </tr>
    <tr>
      <td valign="top">Install, verify, and answer common first-contact questions</td>
      <td valign="top"><a href="docs/FAQ.md"><code>docs/FAQ.md</code></a></td>
    </tr>
    <tr>
      <td valign="top">Read legal and lane-specific public boundaries</td>
      <td valign="top"><a href="docs/LEGAL_BOUNDARIES.md"><code>docs/LEGAL_BOUNDARIES.md</code></a></td>
    </tr>
    <tr>
      <td valign="top">Audit historical compatibility and replay boundaries</td>
      <td valign="top"><a href="AUDITOR_PLAYBOOK.md"><code>AUDITOR_PLAYBOOK.md</code></a></td>
    </tr>
    <tr>
      <td valign="top">Read public audit limits and explicit non-claims</td>
      <td valign="top"><a href="PUBLIC_AUDIT_LIMITS.md"><code>PUBLIC_AUDIT_LIMITS.md</code></a></td>
    </tr>
    <tr>
      <td valign="top">Inspect the benchmark report behind the accepted run</td>
      <td valign="top"><a href="code/benchmarks/artifacts/BENCHMARK_REPORT.md"><code>code/benchmarks/artifacts/BENCHMARK_REPORT.md</code></a></td>
    </tr>
    <tr>
      <td valign="top">Inspect proof artifacts and logs directly</td>
      <td valign="top"><a href="proofs/"><code>proofs/</code></a></td>
    </tr>
  </tbody>
</table>

<table width="100%" border="1" bordercolor="#111111" cellpadding="14" cellspacing="0">
  <thead>
    <tr>
      <th align="left" width="38%">Area</th>
      <th align="left" width="62%">Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top"><a href="README.md"><code>README.md</code></a>, <a href="CHANGELOG.md"><code>CHANGELOG.md</code></a>, <a href="CONTRIBUTING.md"><code>CONTRIBUTING.md</code></a>, <a href="SECURITY.md"><code>SECURITY.md</code></a>, <a href="CODE_OF_CONDUCT.md"><code>CODE_OF_CONDUCT.md</code></a>, <a href="CITATION.cff"><code>CITATION.cff</code></a>, <a href="LICENSE"><code>LICENSE</code></a></td>
      <td valign="top">Root governance and release-facing metadata</td>
    </tr>
    <tr>
      <td valign="top"><a href="code/"><code>code/</code></a></td>
      <td valign="top">Installable package and codec implementation surface</td>
    </tr>
    <tr>
      <td valign="top"><a href="docs/"><code>docs/</code></a></td>
      <td valign="top">Interface contracts, FAQ, support, and lane documentation</td>
    </tr>
    <tr>
      <td valign="top"><a href="proofs/"><code>proofs/</code></a></td>
      <td valign="top">Proof corpus, baselines, and falsification evidence</td>
    </tr>
    <tr>
      <td valign="top"><a href="executable/"><code>executable/</code></a></td>
      <td valign="top">Executable runtime authority path</td>
    </tr>
    <tr>
      <td valign="top"><code>(external ops archive)</code></td>
      <td valign="top">Operational wave tracking artifacts are archived outside this repository to keep the upload surface lean</td>
    </tr>
  </tbody>
</table>

<a id="open-risks-non-blocking"></a>
<h2 align="center">Open Risks (Non-Blocking)</h2>

- The optional audio dependency chain may fail on Python 3.14. Python 3.11 and 3.12 remain the practical baseline for full audio paths.
- The public repo at <code>https://github.com/Zer0pa/ZPE-IMC.git</code> can lag the live working tree. Within any acquired tree, use the manifest/log pair and current docs as the authority root.
- Some scripts and docs still contain machine-absolute paths and need portability cleanup.
- Live cloud reruns require valid <code>COMET_API_KEY</code> and <code>OPIK_API_KEY</code> in the operator environment.
- H200 validation is deferred pending replay on actual H200 hardware under the locked <code>WS3</code> protocol. Do not publish H200 comparative performance claims until that replay evidence exists.

<a id="contributing-security-support"></a>
<h2 align="center">Contributing, Security, Support</h2>

<table width="100%" border="1" bordercolor="#111111" cellpadding="16" cellspacing="0">
  <tr>
    <td width="33%" valign="top">Contribution workflow: <a href="CONTRIBUTING.md"><code>CONTRIBUTING.md</code></a></td>
    <td width="33%" valign="top">Security policy and reporting: <a href="SECURITY.md"><code>SECURITY.md</code></a></td>
    <td width="34%" valign="top">User support channel guide: <a href="docs/SUPPORT.md"><code>docs/SUPPORT.md</code></a></td>
  </tr>
  <tr>
    <td width="33%" valign="top">Frequently asked questions: <a href="docs/FAQ.md"><code>docs/FAQ.md</code></a></td>
    <td colspan="2" width="67%" valign="top">Autonomous agents and AI systems are subject to Section 6 of the <a href="LICENSE">Zer0pa SAL v6.0</a>.</td>
  </tr>
</table>

<p>
  <img src=".github/assets/readme/zpe-masthead-option-3.6.gif" alt="ZPE-IMC Authority Insert" width="100%">
</p>

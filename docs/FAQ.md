<p>
  <img src="../.github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

Organised by reader type. If your question isn't here, open an
issue or see `docs/SUPPORT.md`.

---

<p>
  <img src="../.github/assets/readme/section-bars/architecture-and-theory.svg" alt="ARCHITECTURE AND THEORY" width="100%">
</p>
**What does "Zero-Point" mean?**

Zero-point energy is the irreducible ground state of a quantum
system — the minimum energy that remains even at absolute zero,
which cannot be removed. The name is deliberate: ZPE encodes
information at its irreducible primitive basis. The 20-bit
transport word is a fixed entropy budget. The system's job is to
find the minimum stable primitive set that can carry all modalities
simultaneously without collision, and prove it holds under
adversarial conditions. That is what the D8 invariance gate, the
dirty-data campaigns, and the falsification corpus operationalise.
The physics metaphor has engineering teeth.

---

**Why eight primitives? Why not six or twelve?**

Eight is not a hyperparameter choice. Eight maps to the dihedral
group D₈ — the eight symmetries of the square, the natural closure
group for 2D rotational symmetry. The D8 invariance gate (C3d8)
makes this empirical: deterministic behaviour is proven across all
eight rotations (`rotations_checked: 8`, `status: pass`). The
weighted ablation against P5, P7, P12, and P64 confirms it
quantitatively: P8 scores 99.33 as baseline reference; the nearest
challenger P7 scores 98.70, P12 scores 94.13, P64 scores 91.52.
P5 and P7 lack the D₈ symmetry closure. P12 and P64 add overhead
without gain. Eight is where discrete rotational symmetry and
representational economy converge.

---

**Then why does the mental lane use six primitives (D612)?**

Because cognitive and spatial structure encodes differently from
sensory signal. The mental lane runs D612 — six directional
primitives, twelve structural patterns — validated across COBWEB,
LATTICE, SPIRAL, and TUNNEL topologies. D612 is the first confirmed
case where a lane's optimal N diverges from P8. It is not an
exception to the architecture — it is a demonstration of the
architecture working as designed. A change in N is a profile
variant within the same family, not a separate invention. The
license and project documentation both make this explicit. The space of
N-variants for other lanes and sensoralities is an active research
frontier; D612 is the first data point.

---

**Is ZPE a compression algorithm?**

Not primarily. ZPE is a transport substrate — its job is
deterministic, collision-free routing of heterogeneous modalities
through a shared fixed-width envelope. Compression ratios are
reported for some lanes (touch raw:549, ZPE:87 is a significant
size reduction) but the primary claim is codec integrity:
deterministic roundtrip, adversarial robustness, and verified
external baselines. Size efficiency is a consequence of the
encoding, not the objective. The diagram/image lane explicitly
does not claim universal bitrate dominance — fidelity and
determinism are the verified properties.

---

**What does "IMC" mean and how does it relate to ZPE?**

ZPE is the encoding family. IMC — Integration and Multimodal
Coordination — is the layer that governs how eight transport lane
families (covering ten user-facing modalities) coexist in a single
transport stream. IMC provides the dispatch contract, the
collision-avoidance logic, and the versioned interface that
downstream integrations pin to. ZPE defines the primitives and the
transport word. IMC defines what happens when all eight lane
families are live simultaneously. This repository is the IMC layer.
ZPE-Bio, ZPE-IoT, and other workstreams are downstream consumers of
the IMC contract, not part of it.

---

**What is the wave1.0 contract and why does it matter?**

`wave1.0` is the frozen interface contract for IMC Wave-1. It
defines the canonical mixed-stream authority point (`total_words:
844`), the compatibility vector (SHA256:
`9c8b905f...`), and the lane routing rules that downstream
workstreams must pin to. Freezing the contract means Bio and IoT
can release independently without IMC changes breaking their
integration. If you are building on ZPE-Bio or ZPE-IoT, you pin to
`wave1.0` — not to this repo's internals. The contract is
the stable surface; the implementation beneath it can evolve
within a patch version without breaking downstream consumers. The
`844` stream remains frozen contract truth and a historical demo
anchor; it is not the current March 7 runtime authority path.

---

**What is the current strongest way to read ZPE-IMC?**

As a deterministic, unified, CPU-native multimodal transport system
with three visible authority dimensions:

- Dimension 1: real integrated modality transport across ten
  user-facing modalities on the accepted IMC path
- Dimension 2: a real Rust-enhanced runtime that preserves semantics,
  determinism, proofs, and observability while exceeding the baseline
- Dimension 3: provenance/custody discipline that explains how the
  current authority state emerged without turning archive material into
  live operator truth

The source repo is the current truth surface. Curated upload snapshots
may omit files or carry path defects, and historical/archive material
may carry valuable lineage, but neither outranks the source repo’s
current authority artifacts.

Current public audit acquisition surface:
`https://github.com/Zer0pa/ZPE-IMC.git`. Use that provisioned clone
target rather than the earlier dead clone guidance.

---

**What is the 20-bit transport word and why is it fixed-width?**

The word is partitioned as: mode `[19:18]`, version `[17:16]`,
payload `[15:0]`. Mode encodes NORMAL, ESCAPE, EXTENSION, or
RESERVED. The payload carries lane type-bit markers and the
lane-local symbol code. Fixed-width is a deliberate constraint —
it enforces a finite entropy budget per token, which is what
"ground state" means in engineering terms. Every modality must
fit within the same word. This is what forces the encoding to be
minimal and what makes collision-aware dispatch tractable.

---

**What is a "dirty-data campaign" and why does it matter?**

A dirty-data campaign is an adversarial test run against malformed,
corrupted, or edge-case inputs — designed to find uncaught crashes,
silent corruptions, or undefined behaviour. IMC Wave-1 ran 1,200
cases with 0 uncaught crashes. Individual lane campaigns ran
additional suites (mental: 128 cases, touch: 12 cases, smell: 8
adversarial cases, etc.). This matters because a transport substrate
that only works on clean inputs is not a transport substrate — it is
a demo. The historical dirty-data results live in the source-truth proof warehouse and are not part of this reduced public audit packet.

---

**What is Popperian falsification and why is it in an engineering repo?**

Karl Popper's falsifiability principle holds that a scientific claim
is only meaningful if it can in principle be disproven. This repo
operationalises it as governance: every core claim must survive an
active disproof attempt, not just a happy-path test. Negative
results are retained as first-class artifacts. Claims without
evidence are marked `UNKNOWN`, not omitted. The Open Risks section
in the README is not an embarrassment — it is evidence of rigour.
Serious readers distinguish between projects that hide failures and
projects that document them.

---

<p>
  <img src="../.github/assets/readme/section-bars/setup-and-verification.svg" alt="SETUP AND VERIFICATION" width="100%">
</p>
**How do I install and verify?**

Current front-door posture is a curated repository snapshot ahead of the first
tagged public release. Use the repo clone/install path below for authority
verification, not as packaged public-release guidance.

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
```

Expected current runtime facts:
- `backend='rust'`
- `compiled_extension=True`
- `fallback_used=False`

Current runtime authority is the later March 7 accepted run recorded in
`proofs/logs/phase6_run_of_record_manifest.json` and
`proofs/logs/phase6_comet_run.txt`. The accepted run is
`IMC-Canonical-20260307T131330Z` with `169/169` tests passing and
`benchmark_run_id=A4-BENCH-20260307T131414Z`.

---

**Why do some historical notes mention `780` instead of `844`?**

A historical CLI/executable split was tracked during Wave-1 rehearsal.
Current public status treats that split as historical and closed. The
`844` value remains the frozen `wave1.0` compatibility anchor and a
historical demo truth for downstream pinning, but it is not the current
runtime authority. Use the Rust-backed `run_with_comet.py` path plus the
March 7 manifest/log pair for current operator verification, and use the
family contract when you need the frozen downstream pin.

---

**What Python version should I use?**

Python 3.11 or 3.12. Python 3.14 is supported for core lane
verification but the heavy voice/audio dependency chain may fail
on that path. If you need the full audio stack (music and voice
lanes), use 3.11 or 3.12. Core lanes — text, diagram, image,
mental, touch, smell, taste — are unaffected by the Python 3.14
limitation.

---

**Do I need a GPU?**

No. CPU-only is the verified baseline for all IMC Wave-1 core
lanes. GPU acceleration is tracked for sector workstreams
(Video, XR, Prosody, Bio Wearable) in their respective
repositories. No IMC Wave-1 gate result requires GPU.

---

**I ran `pytest` and saw taste-lane failures. Is that expected?**

This question refers to a historical portability note, not the current
run-of-record. The accepted March 7 authority run records
`tests_total=169`, `tests_passed=169`, and `tests_failed=0` in
`proofs/logs/phase6_comet_run.txt`. Historical taste-lane failures tied
to hardcoded absolute paths remain tracked under
`R-TASTE-LEGACY-PATH-COUPLING` as a path-normalisation risk class and a
lineage caveat, not as the current runtime verdict. If your local run
fails, attach the full pytest output plus the result of
`get_kernel_backend_info()`.

---

<p>
  <img src="../.github/assets/readme/section-bars/integration-and-downstream-use.svg" alt="INTEGRATION AND DOWNSTREAM USE" width="100%">
</p>
**I am building on ZPE-Bio or ZPE-IoT. Where do I start?**

Start with the family contract, not the code:

- `docs/family/IMC_INTERFACE_CONTRACT.md`
- `docs/family/IMC_COMPATIBILITY_VECTOR.json`

Pin to `wave1.0` and SHA256
`9c8b905f6c1d30d057955aa9adf0f7ff9139853494dca673e5fbe69f24fba10e`.
Your workstream's alignment report must reference this vector.
Do not pin to internal package APIs — they may change within a
patch version. The contract surface is stable; the implementation
beneath it is not guaranteed stable at the same timescale.

---

**What does it mean to "pin to the compatibility vector"?**

It means your alignment report records the SHA256 of
`IMC_COMPATIBILITY_VECTOR.json` and declares which version of the
IMC contract your workstream is consuming. If IMC releases a new
vector, downstream workstreams must explicitly update their
alignment report and revalidate. This is how coordinated releases
across independent repos stay consistent without tight coupling.

---

**Can I use ZPE for a domain not listed in the README?**

Yes — the N-primitive directional encoding family is not limited
to the eight transport lane families (covering ten user-facing
modalities) in this repo. The SAL v6.0 and project documentation
explicitly enumerate financial time-series, geospatial, motion
capture, neurological, robotics, video, and IoT as within-scope
domains. The architecture is parameterised by primitive count N and
domain; applying it to a new domain is a Primitive Profile variant,
not a new invention. If you do this, you are operating within the
Protected Architecture and should read `LICENSE` accordingly.

---

<p>
  <img src="../.github/assets/readme/section-bars/evidence-and-claims.svg" alt="EVIDENCE AND CLAIMS" width="100%">
</p>
**How do I verify a specific claim?**

Every non-trivial claim in the technical documentation has an evidence
path pointing to a repo-relative artifact. The entry point for
IMC Wave-1 is:

```text
proofs/IMC_WAVE1_RELEASE_READINESS_REPORT.md
```

For the full evidence index, consult the consolidated proof report:
`proofs/CONSOLIDATED_PROOF_REPORT.md`. Artifact SHA256
hashes in the listed records are the integrity anchors — compute
locally and compare.

---

**What does VERIFIED / INFERRED / UNKNOWN mean in the docs?**

- `VERIFIED` — directly supported by cited artifacts with
  repo-relative evidence paths
- `INFERRED` — coherent synthesis across multiple verified
  artifacts; no single artifact directly supports the claim
- `UNKNOWN` — not evidenced in the cited artifact set; the claim
  is not made

Runtime-state artifacts outrank prose for current operational
truth. If a log file and a prose summary conflict, the log is
authoritative.

---

**What does the mental lane actually encode? Is it reading minds?**

No. The mental lane is a codec-integrity lane. D612 encodes
abstract spatial/cognitive structure — topology classes like
COBWEB, LATTICE, SPIRAL, TUNNEL — as directional primitive
sequences. It is a deterministic codec approximation, not a
biological neural equivalence claim. The scope is explicit: codec
integrity only. No perceptual, cognitive, or clinical equivalence
is claimed or implied. The same scope discipline applies to all
extended modality lanes — smell, taste, and touch are codec-proxy
representations, not receptor-level reconstructions.

---

<p>
  <img src="../.github/assets/readme/section-bars/license-and-ip.svg" alt="LICENSE AND IP" width="100%">
</p>
**Is this open source?**

No. ZPE-IMC is released under the Zer0pa Source-Available License
v6.0 (SAL v6.0), which is not an OSI-approved open-source license.
It is source-available with a delayed open-source conversion: each
version converts automatically to Apache 2.0 three years after its
first public release. Until then: free for individuals, researchers,
open-source projects, and organisations with annual gross revenue
at or under USD 100M. A Commercial License is required above that
threshold or for any Hosted or Managed Service deployment.
Historical release chronology is retained in `CHANGELOG.md` and
`CITATION.cff`. It is not current clone/install guidance for the repo
front door.

---

**What is the "Protected Architecture"?**

The N-primitive directional encoding family and all its profile
variants — including Compass-8 (P8), D612, and any other value
of N applied to any domain. The protection is defined by a
Functional Equivalence Test, not source code similarity. A system
that encodes multimodal information using a finite set of
directional primitives and a shared transport mechanism falls
within scope regardless of what it is called, what language it
is written in, or what value of N it uses. A change in N is a
profile variant within the Protected Architecture, not an
independent invention.

---

**I want a Commercial License. Who do I contact?**

`architects@zer0pa.ai`

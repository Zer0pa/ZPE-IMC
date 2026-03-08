<p>
  <img src="../.github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC MASTHEAD" width="100%">
</p>

<p>
  <img src="../.github/assets/readme/section-bars/what-this-is.svg" alt="WHAT THIS IS" width="100%">
</p>

This document is the canonical architecture index for the accepted IMC runtime.
It defines where transport-contract truth lives and how a fresh operator builds,
verifies, and reruns the current Rust-backed path.

Canonical anchors:
- External auditor acquisition surface: `https://github.com/Zer0pa/ZPE-IMC.git`
- Contact: `architects@zer0pa.ai`
- Contract version: `wave1.0`
- Frozen contract anchor: `total_words=844` for downstream compatibility and historical demo custody only
- Rust kernel crate: `code/rust/imc_kernel`
- Python native adapter: `code/zpe_multimodal/core/imc_native.py`
- Runtime authority path: `./code/rust/imc_kernel/build_install.sh` then `./.venv/bin/python ./executable/run_with_comet.py` in release-default local-only mode
- Runtime authority artifacts: `proofs/logs/phase6_run_of_record_manifest.json` and `proofs/logs/phase6_comet_run.txt`

Historical note:
- `python executable/demo.py` and the older `total_words=844` Wave-1 demo anchor are historical references only. They are not the current operator authority path for the live native backend.

Three dimensions of current authority:
- Dimension 1: integrated modality transport is the primary authority surface.
- Dimension 2: the Rust-enhanced runtime is the subordinate engineering/runtime authority surface.
- Dimension 3: provenance/custody discipline explains the build-up to the current state without turning archive material into live operator truth.

Authority classes:
- Source-repo truth: this repo, its current docs, and `proofs/logs/phase6_run_of_record_manifest.json` plus `proofs/logs/phase6_comet_run.txt`
- Uploaded snapshot defects: the provisioned external auditor snapshot at `https://github.com/Zer0pa/ZPE-IMC.git` can omit files or carry path defects and does not outrank the source repo
- Historical/archive material: chronology and evidence surfaces that inform authority but do not define the live operator path

<p>
  <img src="../.github/assets/readme/section-bars/interface-contracts.svg" alt="INTERFACE CONTRACTS" width="100%">
</p>

| Surface | Role | Canonical path |
|---|---|---|
| Interface contract | Word layout, mode semantics, markers, dispatch precedence | `docs/family/IMC_INTERFACE_CONTRACT.md` |
| Compatibility vector | Machine-readable lock for downstream pinning | `docs/family/IMC_COMPATIBILITY_VECTOR.json` |
| Native kernel build/install | Reproducible Rust wheel build and local install | `code/rust/imc_kernel/build_install.sh` |
| Backend verification | Runtime truth for backend, payload layout, and fallback status | `code/zpe_multimodal/core/imc.py:get_kernel_backend_info` |
| Runtime authority | Canonical execution path for release checks; local-only by default, live observability by explicit opt-in | `executable/run_with_comet.py` |
| Runtime authority evidence | Manifest and wrapper run log | `proofs/logs/phase6_run_of_record_manifest.json`, `proofs/logs/phase6_comet_run.txt` |

<p>
  <img src="../.github/assets/readme/section-bars/word-layout.svg" alt="WORD LAYOUT" width="100%">
</p>

| Envelope field | Bits | Source |
|---|---|---|
| Mode | `[19:18]` | `docs/family/IMC_INTERFACE_CONTRACT.md` |
| Version | `[17:16]` | `docs/family/IMC_INTERFACE_CONTRACT.md` |
| Payload | `[15:0]` | `docs/family/IMC_INTERFACE_CONTRACT.md` |
| Total word | `20` bits | `docs/family/IMC_INTERFACE_CONTRACT.md` |

<p>
  <img src="../.github/assets/readme/section-bars/modality-markers.svg" alt="MODALITY MARKERS" width="100%">
</p>

IMC Wave-1 exposes ten user-facing modalities through eight transport lane
families. Current-facing docs split text and emoji, diagram and image, and
music and voice into separate outward narratives while leaving the shared lane
families and folders unchanged.

| Transport lane family | User-facing modalities covered | Anchor |
|---|---|---|
| `TEXT_EMOJI` | text + emoji | `README.md` modality status table + contract text fallback path |
| `DIAGRAM_IMAGE` | diagram + image | `README.md` modality status table + `docs/family/IMC_INTERFACE_CONTRACT.md` |
| `MUSIC` | music | `README.md` modality status table |
| `VOICE` | voice | `README.md` modality status table |
| `MENTAL` | mental state | `README.md` modality status table |
| `TOUCH` | touch | `README.md` modality status table |
| `SMELL` | smell | `README.md` modality status table |
| `TASTE` | taste | `README.md` modality status table |

<p>
  <img src="../.github/assets/readme/section-bars/dispatch-precedence.svg" alt="DISPATCH PRECEDENCE" width="100%">
</p>

Dispatch order is canonicalized in
`docs/family/IMC_INTERFACE_CONTRACT.md` and mirrored in
`docs/family/IMC_COMPATIBILITY_VECTOR.json`. Any change to marker allocation or
precedence requires contract/version governance updates before public release.

<p>
  <img src="../.github/assets/readme/section-bars/open-risks-non-blocking.svg" alt="OPEN RISKS (NON-BLOCKING)" width="100%">
</p>

Deployment guardrails for architecture consumers:
- The accepted backend verifier must report `backend=rust`, `compiled_extension=1`, and `fallback_used=0`; any other result is a mis-installed runtime, not an accepted fallback.
- Live cloud reruns require valid `COMET_API_KEY` and `OPIK_API_KEY` in the operator environment.
- Physics-layer simulation or equivalence semantics are explicitly out-of-scope for Wave-1 IMC; current scope is transport integrity and reproducible modality routing.

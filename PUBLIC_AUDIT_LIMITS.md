# Public Audit Limits

This note defines what the public ZPE-IMC audit path can and cannot establish.

It is intentionally narrow. It keeps the public audit path honest without reopening
engineering theory, licensing theory, or broad diligence questions.

## What The Public Audit Path Can Establish

- the current provisioned acquisition surface
- the current native runtime path (`backend='rust'`, `compiled_extension=True`, `fallback_used=False`)
- the identity of the accepted March 7 run-of-record
- the current benchmark/run identity and throughput ceiling
- the current three-dimension story:
  - real modality integration
  - real Rust-backed runtime authority
  - real provenance/custody discipline

## What The Public Audit Path Does Not Establish

- peer-reviewed scientific novelty
- external academic validation
- H200 comparative performance
- a guarantee that every uploaded public snapshot is identical to the live working tree
- broader founder/team/commercial diligence outside the shipped public docs

## Public Audit Limits Matrix

| Limit | Current public state | Why it matters |
|---|---|---|
| Snapshot lag | The provisioned external auditor snapshot can lag the live working tree. | Outsiders may be looking at a weaker surface than the operator cites. |
| Historical absolute paths | Some historical proof artifacts still contain machine-absolute paths. | Historical artifacts are evidence lineage, not ideal portable run instructions. |
| Anchor density | `780`, `844`, `wave1.0`, and the March 7 run all coexist. | Without an authority matrix, readers can blur history, compatibility, and current truth. |
| Private telemetry surfaces | Comet/Opik URLs are operator surfaces, not the public evidentiary root. | Public audit should rely on local shipped artifacts instead. |
| H200 claims | Explicitly deferred. | No H200 comparison should be treated as admissible public evidence yet. |
| Scientific validation | No external scientific validation packet ships here. | Engineering proof is not the same thing as settled scientific novelty. |
| Separate public audit harness | No standalone `public_audit.sh` or reduced public suite ships in the current tree. | The public audit path is a documented workflow, not a one-command bundle. |

## Feature Flags And Keys

No manual feature flags are required for the recommended public audit path in `AUDITOR_PLAYBOOK.md`.

Why:
- `executable/run_with_comet.py` sets the required modality flags internally
- the public helper/demo path uses `require_env=False` where appropriate

Flags still relevant outside the recommended path:
- `STROKEGRAM_ENABLE_DIAGRAM`
- `STROKEGRAM_ENABLE_MUSIC`
- `STROKEGRAM_ENABLE_VOICE`

Those matter when a reviewer directly instantiates `IMCEncoder()` with its
default `require_env=True` behavior.

No manual telemetry keys are required for the public audit path:
- `COMET_API_KEY` is optional
- `OPIK_API_KEY` is optional

## Honest Reading Rules

- Read `844` as compatibility truth and historical demo custody, not as the current runtime verdict.
- Read March 7 manifest/log artifacts as the current operator truth.
- Read throughput numbers as `imc_stream_words/sec`, not natural-language words/sec.
- Read image performance as deterministic mixed-stream transport evidence, not commodity image-codec supremacy.
- Read smell and taste as real but bounded lanes, not unconstrained general claims.
- Read the shipped Triton ONNX model as publicly auditable against its committed integrity manifest, not against the excluded `proofs/artifacts/**` warehouse.
- Read byte-for-byte comparison against the A6 export as operator/private replay only.

## Use These Files Together

- `AUDITOR_PLAYBOOK.md`
- `README.md`
- `docs/FAQ.md`
- `docs/ARCHITECTURE.md`
- `proofs/logs/phase6_run_of_record_manifest.json`
- `proofs/logs/phase6_comet_run.txt`

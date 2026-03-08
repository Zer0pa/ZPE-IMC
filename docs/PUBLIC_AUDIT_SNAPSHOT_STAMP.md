# Public Audit Snapshot Stamp
Date: 2026-03-09

## Source Commit Base
- Source repo: `/Users/Zer0pa/ZPE-IMC-REPO`
- Source HEAD commit base: `e316ddd77805fc59040b9d6a687c1241fe40eabc`
- Source working-tree state at snapshot build: dirty (`215` entries in `git status --porcelain`)

## Completeness Declaration
This public audit snapshot was rebuilt from the current working source truth in `/Users/Zer0pa/ZPE-IMC-REPO`, not from a blind push of the mixed source git tree.

Included as current authority-bearing public surfaces:
- current front-door, legal, package-facing, and audit-facing docs
- current front-door README nav asset bundle
- current wrapper/package invocation hygiene:
  - `executable/__init__.py`
- current Triton public-audit fix surfaces:
  - `code/tests/test_triton_repo_layout.py`
  - `code/tests/test_triton_repo_layout_operator.py`
  - `code/deployment/triton/model_repository/zpe_tokenizer_onnx/1/model.integrity.json`
- current benchmark artifacts under `code/benchmarks/artifacts`
- current Phase 6 runtime authority artifacts under `proofs/logs/phase6_*`
- current release-validation security report

Intentionally excluded from this reduced public audit snapshot:
- `agent_ops/**`
- `v0.0/**`
- `code/source/**`
- `proofs/artifacts/**` warehouse bundles
- `proofs/runbooks/**`
- historical proof logs outside `proofs/logs/phase6_*`
- historical proof-summary roots replaced by the current manifest/log authority pair
- local caches, bytecode, build residue, and Rust target directories

## Manifest Pointer
- Run-of-record manifest: `proofs/logs/phase6_run_of_record_manifest.json`
- Runtime log: `proofs/logs/phase6_comet_run.txt`

## Supersession
- Supersedes earlier public snapshot commit: `89e9edbc62f046653daec3f5410205cfd7f78628`
- Reason: the earlier public head still mixed older live-Comet authority language with newer local proof anchors, still routed several docs at `ZPE-Test`, and did not yet carry the latest README nav asset bundle or wrapper package-hygiene fix

## Sync Target
- Public audit repo: `https://github.com/Zer0pa/ZPE-IMC`
- Target branch: `main`

## Staging Note
This snapshot carries staged public-surface normalization so that acquisition URLs point at the live public audit repo and public docs do not imply omitted warehouse/runbook material ships in this reduced packet.

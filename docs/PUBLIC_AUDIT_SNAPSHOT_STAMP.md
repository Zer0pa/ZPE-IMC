# Public Audit Snapshot Stamp
Date: 2026-03-07

## Source Commit Base
- Source repo: `/Users/Zer0pa/ZPE-IMC-REPO`
- Source HEAD commit: `e316ddd77805fc59040b9d6a687c1241fe40eabc`
- Source working tree state at snapshot build: dirty (`187` entries in `git status --porcelain`)

## Completeness Declaration
This public audit snapshot was built from the current working source truth, not from a blind push of the mixed source git tree.

Included as current authority-bearing public surfaces:
- current front-door, legal, and package-facing docs
- current code, tests, fixtures, examples, executable helpers, and workflow surfaces required by the live source tree
- current benchmark artifacts under `code/benchmarks/artifacts`
- current Phase 6 runtime authority artifacts under `proofs/logs/phase6_*`
- current release-validation security report

Intentionally excluded from this public audit snapshot:
- `agent_ops/**`
- `v0.0/**`
- `proofs/artifacts/**` warehouse bundles
- `proofs/runbooks/**`
- historical proof logs outside `proofs/logs/phase6_*`
- historical proof-summary roots replaced by current Phase 6 authority artifacts
- local caches, bytecode, build residue, and Rust target directories

## Manifest Pointer
- Run-of-record manifest: `proofs/logs/phase6_run_of_record_manifest.json`
- Runtime log: `proofs/logs/phase6_comet_run.txt`

## Sync Target
- Public audit repo: `https://github.com/Zer0pa/ZPE-IMC`
- Target branch: `main`

## Staging Note
This snapshot includes a staging-only public-surface normalization pass so that acquisition URLs point at the live public audit repo rather than the earlier `ZPE-Test` rehearsal surface.

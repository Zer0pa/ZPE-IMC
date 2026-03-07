<p>
  <img src=".github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

ZPE-IMC welcomes contributions from researchers, engineers, and
adversarial testers. This document covers everything you need to
contribute effectively — from environment setup through the PR
process.

Read this before opening a PR. The bar here is evidence, not
intention.

---

<p>
  <img src=".github/assets/readme/section-bars/before-you-start.svg" alt="BEFORE YOU START" width="100%">
</p>
ZPE-IMC operates under a falsification-first culture. This means:

- Negative results are first-class artifacts. If your contribution
  finds a failure, that finding is valuable — do not suppress it.
- Claims require evidence. A PR that asserts improvement without
  a comparator artifact will not be merged.
- Dirty-data and adversarial test cases are welcome and encouraged.
  Contributions that extend adversarial coverage raise the floor for
  everyone.

If you are building a downstream integration on ZPE-Bio or ZPE-IoT,
you do not need to contribute here. Pin to the wave1.0 compatibility
vector and work within your own workstream. Changes to the IMC
integration contract are governed by the family contract process,
not individual PRs.

---

<p>
  <img src=".github/assets/readme/section-bars/licensing-of-contributions.svg" alt="LICENSING OF CONTRIBUTIONS" width="100%">
</p>
By submitting a contribution you agree that:

- Your contribution is licensed to Zer0pa under the terms of the
  Zer0pa Source-Available License v6.0 (SAL v6.0).
- You retain copyright in your contribution.
- You grant Zer0pa a perpetual, worldwide, royalty-free, irrevocable
  license to use, modify, reproduce, distribute, sublicense, and
  commercially exploit your contribution as part of the Software.
- You represent that you have the legal right to make the
  contribution and that it does not violate any third-party rights.
- If you or your organisation's annual gross revenue exceeds
  USD 100M, a Commercial License is required before contributing to
  production deployments. See `LICENSE` for full terms and contact
  `architects@zer0pa.ai` for legal/licensing queries.
- `LICENSE` is the legal source of truth. This section is a plain
  summary and is not legal advice.

The contributor patent non-assertion clause in SAL v6.0 Section 7
applies. Read it before contributing if you hold relevant patents.

---

<p>
  <img src=".github/assets/readme/section-bars/environment-setup.svg" alt="ENVIRONMENT SETUP" width="100%">
</p>
**Recommended contributor path:** Python 3.11 or 3.12.
If you use a different Python version, include version details and
command output in your PR evidence.

Current public audit/contributor acquisition surface:
`https://github.com/Zer0pa/ZPE-IMC.git`

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
```

Verify your environment:

For the current operator-style proof rerun, use:

```bash
python ./executable/run_with_comet.py
```

Expected backend facts:
- `backend='rust'`
- `compiled_extension=True`
- `fallback_used=False`

If you do not see that backend state, include the command output and
environment details in your issue or PR so maintainers can triage the
runtime divergence. The `844` Wave-1 demo remains frozen contract /
historical demo truth only; it is not the current contributor authority
path.

---

<p>
  <img src=".github/assets/readme/section-bars/running-the-test-suite.svg" alt="RUNNING THE TEST SUITE" width="100%">
</p>
```bash
pytest code
```

All tests must pass before a PR is opened. The accepted March 7
run-of-record records `169/169` tests PASS in
`proofs/logs/phase6_comet_run.txt`. One historical portability note
remains open as lineage, not as the current authority verdict:

Public Triton integrity rule:
- the public test surface validates `code/deployment/triton/model_repository/zpe_tokenizer_onnx/1/model.onnx` against the committed `model.integrity.json`
- the byte-for-byte comparison against `proofs/artifacts/2026-02-24_program_maximal/A6/exported/zpe_tokenizer_op.onnx` is operator/private only and cleanly skips when that proof export is excluded from the snapshot

- Historical taste-lane failures tied to legacy absolute paths were
  tracked as `R-TASTE-LEGACY-PATH-COUPLING`. Do not fix this class of
  issue by hardcoding your own paths — the correct fix is path
  normalisation. Keep the March 7 `169/169` authority result distinct
  from that historical risk lineage and use `PUBLIC_AUDIT_LIMITS.md`
  plus the current manifest/log pair as the public packet authority
  root.

CI runs `imc-ci.yml` on every PR. Your PR must pass CI before
review begins. No exceptions.

Open contribution targets backed by the current Wave-1 evidence set:

<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Target</th>
      <th align="left">Current status</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>`R-IMC-Q103-LICENSE-BOUNDARY`</td><td>OPEN (non-blocking for Q100/Q101/Q102/Q104)</td></tr>
    <tr><td>`R-IMC-GLOBAL-REGRESSION-SINGLE-PROOF`</td><td>OPEN; global sentence remains UNVERIFIED without one consolidated artifact</td></tr>
    <tr><td>`R-TASTE-LEGACY-PATH-COUPLING`</td><td>OPEN non-blocking; historical portability lineage only, not the March 7 run-of-record verdict</td></tr>
    <tr><td>IoT deferred preflight + augmented delta closure</td><td>Preflight deferred `1`; augmentation delta has `1` fail claim pending closure</td></tr>
    <tr><td>GPU-fleet readiness in sector lanes</td><td>`NO` for Ink, Prosody, XR, Bio Wearable</td></tr>
  </tbody>
</table>

If you are proposing an N-variant profile change (where `N != 8`),
include a side-by-side profile score comparison against the current
P8 baseline (`P8=99.33`), plus your dataset scope, scoring method,
and failure cases. N-variant proposals without this evidence package
will be treated as incomplete.

---

<p>
  <img src=".github/assets/readme/section-bars/what-we-accept.svg" alt="WHAT WE ACCEPT" width="100%">
</p>
**Bug fixes** — with a reproduction case and evidence that the fix
resolves it without regressing anything else.

**Adversarial test cases** — extensions to the dirty-data campaign,
new malformed input profiles, edge cases in lane routing or
collision handling. These do not require a fix — a well-documented
failure finding is a valid contribution.

**Path portability fixes** — normalising machine-absolute paths to
repo-relative paths. See `R-PATH-PORTABILITY` in the risk register.

**Documentation corrections** — factual errors, broken links,
outdated evidence paths. Evidence-backed corrections only.

**Touch comparator coverage** — additional body-region and z-layer
external baseline cases. See `R-TOUCH-COMPARATOR-COVERAGE`.

---

<p>
  <img src=".github/assets/readme/section-bars/what-we-do-not-accept.svg" alt="WHAT WE DO NOT ACCEPT" width="100%">
</p>
- Changes to the wave1.0 interface contract or compatibility vector
  without an explicit family coordination process involving Bio
  and IoT workstreams
- PRs that inflate codec integrity claims into human-equivalence
  claims (scope discipline is a hard constraint — see `README.md`
  and `PUBLIC_AUDIT_LIMITS.md`)
- PRs without a passing CI run
- PRs without evidence artifacts where the change touches codec
  behaviour, gate logic, or integration contracts
- Changes that alter, suppress, or remove failing or INCONCLUSIVE
  test results from the proof corpus

---

<p>
  <img src=".github/assets/readme/section-bars/pr-process.svg" alt="PR PROCESS" width="100%">
</p>
1. **Fork and branch** — branch from `main`; use a descriptive
   branch name (`fix/taste-path-portability`,
   `test/touch-comparator-z-layer`, etc.)

2. **Make your change** — keep scope tight; one concern per PR

3. **Run tests** — `pytest code`; if your change touches runtime or
   backend paths, rebuild the Rust kernel and verify
   `get_kernel_backend_info()` still reports `backend='rust'`,
   `compiled_extension=True`, and `fallback_used=False`

4. **Add evidence** — if your change touches codec behaviour,
   include before/after metrics, a claim status delta, or a
   falsification result as appropriate; attach evidence in the PR and
   keep it aligned to the current shipped proof surface. The historical
   `proofs/artifacts/` warehouse is not part of this reduced public
   audit snapshot.

5. **Open the PR** — use the PR template; fill every field; do not
   leave the evidence section blank if your change is
   behaviour-affecting

6. **CI must pass** — `imc-ci.yml` runs automatically; a failing
   CI run will not be reviewed

7. **Review** — a maintainer will review for evidence quality,
   scope discipline, and compatibility vector integrity; expect
   questions on evidence if the artifact trail is thin

---

<p>
  <img src=".github/assets/readme/section-bars/commit-style.svg" alt="COMMIT STYLE" width="100%">
</p>
- Present tense, imperative mood: `Fix taste path portability`,
  not `Fixed` or `Fixes`
- Reference the risk ID if addressing a known issue:
  `Fix path portability (R-PATH-PORTABILITY)`
- Keep commits atomic — one logical change per commit

---

<p>
  <img src=".github/assets/readme/section-bars/issues.svg" alt="ISSUES" width="100%">
</p>
Before opening an issue, check:

- The Open Risks section in `README.md` — your issue may already
  be documented and adjudicated
- `PUBLIC_AUDIT_LIMITS.md` — for current public-packet limits and
  known auditor-facing boundaries

Use the issue templates in `.github/ISSUE_TEMPLATE/`. An issue
without a reproducible case or an evidence path will be closed
with a request for more information.

---

<p>
  <img src=".github/assets/readme/section-bars/questions.svg" alt="QUESTIONS" width="100%">
</p>
See `SECURITY.md` for vulnerability reporting. For all other
questions, see `docs/SUPPORT.md` and use the Question template.

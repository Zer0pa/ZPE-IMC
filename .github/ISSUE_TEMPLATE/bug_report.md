---
name: Bug Report
about: Something is broken — codec failure, crash, wrong output
labels: bug
assignees: ''
---

<p>
  <img src="../assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

<p>
  <img src="../assets/readme/section-bars/bug-report.svg" alt="BUG REPORT" width="100%">
</p>


**Describe the bug**
A clear description of what is broken and what you expected instead.

**Component**
Which component is affected?

- [ ] `zpe_multimodal` package
- [ ] A specific lane (specify: _________)
- [ ] CLI (`zpe-imc`)
- [ ] CI/CD workflow
- [ ] Proof corpus / artifact
- [ ] Documentation

**Workstream scope**
Disambiguate where this bug should be triaged:

- [ ] IMC core repository scope
- [ ] ZPE-IoT downstream alignment scope
- [ ] ZPE-Bio downstream alignment scope
- [ ] Unsure (maintainer help requested)

**To reproduce**
Exact commands and inputs to reproduce the issue

**Expected output**
What should have happened.

**Actual output**
What actually happened. Include full error output.

**Verification check**
Before filing: does `python executable/demo.py` still emit
`total_words: 844`? If not, attach the exact output and full
environment details for triage.

- [ ] Yes — `844` confirmed
- [ ] No — output differs (details attached)

**Environment**

- Python version:
- OS:
- Install method (`pip install -e` / other):
- Relevant dependency versions:

**Lane baseline metric field (if applicable)**

- Baseline lane/workstream:
- Canonical demo words observed:
- Core test count observed:
- Lane-specific baseline metric observed (e.g., strict DT, comparator cases, PRD):

**Evidence**
If this touches codec behaviour, attach or link before/after
metrics, logs, or a minimal reproducible artifact. A bug report
without a reproducible case will be closed with a request for
more information.

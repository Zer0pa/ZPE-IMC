---
name: Evidence Dispute
about: A claim in the proof corpus or documentation
       is inconsistent with the artifacts
labels: evidence, dispute
assignees: ''
---

<p>
  <img src="../assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

<p>
  <img src="../assets/readme/section-bars/evidence-dispute.svg" alt="EVIDENCE DISPUTE" width="100%">
</p>


**Claim under dispute**
Quote the exact claim and its source (file path and line or
section).

**Evidence that contradicts it**
Provide the artifact path, hash, or log output that conflicts
with the claim. Counter-evidence is required — assertions without
artifacts will not be adjudicated.

**Claim status in your assessment**

- [ ] Should be VERIFIED → INFERRED
- [ ] Should be VERIFIED → UNKNOWN
- [ ] Should be INFERRED → UNKNOWN
- [ ] Scope inflation — claim exceeds what evidence supports
- [ ] Factual error — numbers or paths are wrong
- [ ] Other (describe):

**Status semantics implicated (check all that apply)**

- [ ] VERIFIED (directly supported by cited artifacts)
- [ ] INFERRED (coherent synthesis across verified artifacts)
- [ ] UNKNOWN (not evidenced in cited artifacts)
- [ ] GO_QUALIFIED (supported with stated boundaries)
- [ ] INCONCLUSIVE (evidence conflict not reconciled)
- [ ] NO_GO/FAIL (core gates unresolved)
- [ ] PARKED_BY_POLICY (intentionally deferred scope)

**Suggested correction**
What should the claim say, and what evidence supports that
correction?

**Note**
This template is for evidence integrity issues only. For codec
bugs use the Bug Report template. For new capabilities use the
Feature Request template.

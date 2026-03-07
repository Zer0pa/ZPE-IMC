<p>
  <img src="../.github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

Navigation index for the ZPE-IMC Wave-1 documentation surface.

This directory contains the interface contracts, family alignment
artifacts, runbooks, and release notes that govern how ZPE-IMC is
consumed by downstream integrations and how the Wave-1 release was
adjudicated. The proof corpus lives in `proofs/` — see the
pointer at the bottom of this file.

---

<p>
  <img src="../.github/assets/readme/section-bars/faq-and-support.svg" alt="FAQ AND SUPPORT" width="100%">
</p>
<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Document</th>
      <th align="left">What it is</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`docs/FAQ.md`</td>
      <td>Public frequently asked questions for architecture, verification, and integration</td>
    </tr>
    <tr>
      <td>`AUDITOR_PLAYBOOK.md`</td>
      <td>Shortest outsider verification path for the current public audit surface</td>
    </tr>
    <tr>
      <td>`PUBLIC_AUDIT_LIMITS.md`</td>
      <td>Public-vs-private boundary note, expected limits, and current audit honesty constraints</td>
    </tr>
    <tr>
      <td>`docs/SUPPORT.md`</td>
      <td>Public support routing and response expectations</td>
    </tr>
  </tbody>
</table>

---

<p>
  <img src="../.github/assets/readme/section-bars/interface-contracts.svg" alt="INTERFACE CONTRACTS" width="100%">
</p>
The authoritative surface for downstream consumers (ZPE-Bio, ZPE-IoT,
sector integrations). Pin to these — not to package internals.

<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Document</th>
      <th align="left">What it is</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`family/IMC_INTERFACE_CONTRACT.md`</td>
      <td>Full wave1.0 interface specification — the contract that downstream integrations are bound to</td>
    </tr>
    <tr>
      <td>`family/IMC_COMPATIBILITY_VECTOR.json`</td>
      <td>Machine-readable compatibility anchor; SHA256 `9c8b905f6c1d30d057955aa9adf0f7ff9139853494dca673e5fbe69f24fba10e`</td>
    </tr>
    <tr>
      <td>`family/IMC_RELEASE_NOTE_FOR_BIO_IOT.md`</td>
      <td>Handoff note to ZPE-Bio and ZPE-IoT — what changed, what is frozen, what they must pin to</td>
    </tr>
  </tbody>
</table>

If you are building a downstream integration, `IMC_INTERFACE_CONTRACT.md`
is your starting point. The compatibility vector SHA256 is the
coordination anchor — your alignment report must reference it.

---

<p>
  <img src="../.github/assets/readme/section-bars/runbooks.svg" alt="RUNBOOKS" width="100%">
</p>
Operational Wave-1 runbooks are part of source-truth execution lineage,
but they are intentionally omitted from this reduced public audit
snapshot. Use `AUDITOR_PLAYBOOK.md`, `PUBLIC_AUDIT_LIMITS.md`, and the
Phase 6 manifest/log pair as the current public audit path.

---

<p>
  <img src="../.github/assets/readme/section-bars/release-notes.svg" alt="RELEASE NOTES" width="100%">
</p>
<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Document</th>
      <th align="left">What it is</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`docs/family/IMC_RELEASE_NOTE_FOR_BIO_IOT.md`</td>
      <td>Wave-1 release summary for external consumption</td>
    </tr>
  </tbody>
</table>

---

<p>
  <img src="../.github/assets/readme/section-bars/family-alignment.svg" alt="FAMILY ALIGNMENT" width="100%">
</p>
How ZPE-Bio and ZPE-IoT align to this contract. These are their
artifacts, referenced here for traceability.

<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Workstream</th>
      <th align="left">Alignment report</th>
      <th align="left">Compatibility vector</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>ZPE-Bio</td>
      <td>`BIOIMCALIGNMENTREPORT.md` (in ZPE-Bio repo)</td>
      <td>`BIOCOMPATIBILITYVECTOR.json`</td>
    </tr>
    <tr>
      <td>ZPE-IoT</td>
      <td>`IOTIMCALIGNMENTREPORT.md` (in ZPE-IoT repo)</td>
      <td>`IOTCOMPATIBILITYVECTOR.json`</td>
    </tr>
  </tbody>
</table>

Both workstreams consume IMC wave1.0. Their alignment artifacts confirm
consumption of the compatibility vector SHA256 above.

---

<p>
  <img src="../.github/assets/readme/section-bars/proof-corpus.svg" alt="PROOF CORPUS" width="100%">
</p>
The full evidence archive — lane baselines, falsification results, wave
readiness reports, HOP falsification records, artifacts, logs — lives here:

```text
proofs/
```

Entry points:

<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Document</th>
      <th align="left">What it is</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`proofs/IMC_WAVE1_RELEASE_READINESS_REPORT.md`</td>
      <td>Top-level wave readiness verdict; phase gates, regression, dirty-data campaign</td>
    </tr>
    <tr>
      <td>`proofs/CONSOLIDATED_PROOF_REPORT.md`</td>
      <td>Full consolidated proof corpus</td>
    </tr>
    <tr>
      <td>`proofs/release_validation/security/secret_scan_report_20260225T104355Z.md`</td>
      <td>Secret scan report for the Wave-1 release packet</td>
    </tr>
    <tr>
      <td>`proofs/logs/hop_claim_matrix.md`</td>
      <td>HOP claim-matrix falsification record</td>
    </tr>
  </tbody>
</table>

The proof corpus is the evidentiary spine of this release. If a claim
is made about IMC Wave-1, the supporting artifact is in `proofs/`.

---

<p>
  <img src="../.github/assets/readme/section-bars/engineering-references.svg" alt="ENGINEERING REFERENCES" width="100%">
</p>
Use these stable in-repo references for claim vocabulary, evidence
status (`VERIFIED`, `INFERRED`, `UNKNOWN`), and falsification posture:

- `proofs/CONSOLIDATED_PROOF_REPORT.md`
- `proofs/logs/hop_claim_matrix.md`

---

<p>
  <img src="../.github/assets/readme/section-bars/what-this-directory-is-not.svg" alt="WHAT THIS DIRECTORY IS NOT" width="100%">
</p>
This directory does not contain:

- **ZPE-Bio or ZPE-IoT documentation** — those live in their own repos
- **Sector lane documentation** — sector lanes are governed by the
  central adjudication board in `zpe-lab-data`
- **Agent ops artifacts** — wave tracking, gate decisions, and review
  artifacts are kept in an external ops archive, not in this repo

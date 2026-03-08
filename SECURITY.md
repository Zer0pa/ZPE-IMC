<p>
  <img src=".github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

<p>
  <img src=".github/assets/readme/section-bars/scope.svg" alt="SCOPE" width="100%">
</p>
This document covers vulnerability reporting for the ZPE-IMC
package and its proof corpus. It does not cover downstream
workstreams (ZPE-Bio, ZPE-IoT) — report vulnerabilities in those
repos directly.

Current provisioned external auditor acquisition surface:
`https://github.com/Zer0pa/ZPE-IMC.git`

What counts as a security issue in this repo:

- Vulnerabilities in the `zpe_multimodal` package that could allow
  arbitrary code execution, data exfiltration, or privilege
  escalation
- Secrets, credentials, or tokens inadvertently committed to the
  repo or proof artifacts
- Dependency vulnerabilities in the package's declared dependencies
- Issues in the CI/CD workflows (`imc-ci.yml`, `imc-release.yml`)
  that could allow supply chain compromise

What does not count as a security issue:

- Codec integrity failures or lane regression failures — these are
  engineering issues; open a standard bug report via the issue
  templates
- Falsification findings or negative test results — these are
  first-class artifacts; open a standard issue or submit a PR with
  evidence
- Claims disputes about documented project evidence — open a
  standard issue using the evidence dispute template

---

<p>
  <img src=".github/assets/readme/section-bars/reporting-a-vulnerability.svg" alt="REPORTING A VULNERABILITY" width="100%">
</p>
**Do not open a public issue for a security vulnerability.**

Report privately through the maintainer email:

- **`architects@zer0pa.ai`**

Include in your report:

- A clear description of the vulnerability
- The affected component (package, workflow, artifact, dependency)
- Steps to reproduce or a proof of concept
- Your assessment of severity and impact
- Any suggested remediation, if you have one

---

<p>
  <img src=".github/assets/readme/section-bars/response-commitment.svg" alt="RESPONSE COMMITMENT" width="100%">
</p>
<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Stage</th>
      <th align="left">Target timeframe</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Acknowledgement</td>
      <td>Within 48 hours of receipt</td>
    </tr>
    <tr>
      <td>Initial assessment</td>
      <td>Within 7 days</td>
    </tr>
    <tr>
      <td>Remediation or mitigation plan</td>
      <td>Within 30 days for confirmed issues</td>
    </tr>
    <tr>
      <td>Public disclosure</td>
      <td>Coordinated with reporter; minimum 90 days</td>
    </tr>
  </tbody>
</table>

We follow coordinated disclosure. We will not take legal action
against researchers who report vulnerabilities in good faith and
follow this policy.

---

<p>
  <img src=".github/assets/readme/section-bars/secret-scan.svg" alt="SECRET SCAN" width="100%">
</p>
A Wave-1 secret-scan report is published at:
`proofs/release_validation/security/secret_scan_report_20260225T104355Z.md`

<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Gate context</th>
      <th align="left">Current policy handle</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Security claim traceability</td><td>Every non-trivial technical claim should include explicit evidence paths</td></tr>
    <tr><td>Secret-scan evidence path</td><td><code>proofs/release_validation/security/secret_scan_report_20260225T104355Z.md</code></td></tr>
    <tr><td>Insufficient evidence handling</td><td>Use `UNKNOWN` or `INCONCLUSIVE` until artifact support is available</td></tr>
  </tbody>
</table>

If you find a secret that was missed, report it via the private
channel above — not as a public issue.

---

<p>
  <img src=".github/assets/readme/section-bars/supported-versions.svg" alt="SUPPORTED VERSIONS" width="100%">
</p>
<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Version</th>
      <th align="left">Supported</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`0.0.1` (Wave-1)</td>
      <td>✅ Current — actively supported</td>
    </tr>
    <tr>
      <td>Earlier internal versions</td>
      <td>❌ Not supported</td>
    </tr>
  </tbody>
</table>

Security fixes will be released as patch versions (`0.0.x`) and
documented in `CHANGELOG.md`.

---

<p>
  <img src=".github/assets/readme/section-bars/out-of-scope.svg" alt="OUT OF SCOPE" width="100%">
</p>
The following are explicitly out of scope for this security policy:

- External publication channels for defensive disclosures
- The SAL v6.0 license text — direct licensing questions to
  `architects@zer0pa.ai`
- Third-party dependencies — report upstream; we will track and
  update as needed

`LICENSE` is the legal source of truth for licensing terms. This
security policy is an operational summary and is not legal advice.

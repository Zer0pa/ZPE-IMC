<p>
  <img src="assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

<p>
  <img src="assets/readme/section-bars/summary.svg" alt="SUMMARY" width="100%">
</p>
What does this PR do? One or two sentences.

<p>
  <img src="assets/readme/section-bars/type-of-change.svg" alt="TYPE OF CHANGE" width="100%">
</p>
- [ ] Bug fix
- [ ] Adversarial test case / dirty-data extension
- [ ] Path portability fix
- [ ] Documentation correction
- [ ] Feature / lane extension
- [ ] Other (describe):

<p>
  <img src="assets/readme/section-bars/linked-issue.svg" alt="LINKED ISSUE" width="100%">
</p>
Closes # (if applicable)

<p>
  <img src="assets/readme/section-bars/verification.svg" alt="VERIFICATION" width="100%">
</p>
- [ ] `python executable/demo.py` emits `total_words: 844`
- [ ] `pytest code` passes, or any failures are documented
      with full output and artifact paths for triage
- [ ] CI (`imc-ci.yml`) passes
- [ ] Latest core runtime check remains `153/153` tests passed
- [ ] If release-scoped behaviour changed, include scoped regression
      result (baseline: `52/52` PASS)

Authority anchor for the canonical stream check:
`proofs/logs/phase6_comet_run.txt`

Lane-specific regression guardrails (complete rows for lanes touched):

<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Lane</th>
      <th align="left">Baseline snapshot</th>
      <th align="left">Your post-change result</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Text / Emoji</td><td><code>pytest=9</code> passed</td><td></td></tr>
    <tr><td>Diagram / Image</td><td><code>pytest=16</code> passed; enhancement PSNR <code>45.9517886080</code> dB</td><td></td></tr>
    <tr><td>Music / Voice</td><td>Events <code>4</code>; packed words <code>34</code>; command return code <code>0</code></td><td></td></tr>
    <tr><td>Mental</td><td><code>pytest=28</code> passed</td><td></td></tr>
    <tr><td>Touch</td><td><code>pytest=20</code> passed</td><td></td></tr>
    <tr><td>Smell</td><td>Comparator cases <code>116</code>; Q-103 license boundary remains active</td><td></td></tr>
    <tr><td>Taste</td><td>Merged unique InChIKey <code>13510</code>; known legacy-path failures <code>2</code></td><td></td></tr>
  </tbody>
</table>

<p>
  <img src="assets/readme/section-bars/evidence.svg" alt="EVIDENCE" width="100%">
</p>
If this PR touches codec behaviour, gate logic, or integration
contracts, list the artifacts below. A behaviour-affecting PR
without evidence will not be merged.

<table width="100%" border="1" bordercolor="#b8c0ca" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <th align="left">Artifact</th>
      <th align="left">Path</th>
      <th align="left">Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Before/after metrics</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <td>Claim status delta</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <td>Falsification result</td>
      <td></td>
      <td></td>
    </tr>
  </tbody>
</table>

If no evidence is required (docs fix, path normalisation, etc.),
state why:

<p>
  <img src="assets/readme/section-bars/compatibility-vector-impact.svg" alt="COMPATIBILITY VECTOR IMPACT" width="100%">
</p>
Does this PR require a change to the wave1.0 compatibility vector
or interface contract?

- [ ] No
- [ ] Yes — (describe the coordination impact on ZPE-Bio and
      ZPE-IoT and confirm family coordination has been initiated)

<p>
  <img src="assets/readme/section-bars/scope-discipline.svg" alt="SCOPE DISCIPLINE" width="100%">
</p>
- [ ] This PR does not inflate claims beyond what the evidence
      supports
- [ ] No human-equivalence, clinical, or regulatory claims are
      introduced

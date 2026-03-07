<p>
  <img src=".github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC MASTHEAD" width="100%">
</p>

<p>
  <img src=".github/assets/readme/section-bars/release-notes.svg" alt="RELEASING" width="100%">
</p>

This document defines the public release gate and decision boundary for ZPE-IMC Wave-1.

Canonical anchors:
- Repository: `https://github.com/zer0pa/zpe-imc`
- Contact: `architects@zer0pa.ai`

<p>
  <img src=".github/assets/readme/section-bars/scope.svg" alt="SCOPE" width="100%">
</p>

Release statements in this repository are bounded to evidence-backed technical claims and published status semantics.

Evidence IDs: `C001`, `C040`, `C042`, `C043`, `C045`, `C046`

<p>
  <img src=".github/assets/readme/section-bars/verification.svg" alt="VERIFICATION" width="100%">
</p>

| Gate | Required state | Evidence |
|---|---|---|
| Canonical runtime anchor | `total_words 844`, `153/153` tests passed, deterministic hash match | `C009`, `M001`, `M003`, `M004`, `M005` |
| IMC readiness gate | `GO`; phase gates `7/7` PASS; scoped regression `52/52` PASS | `C048`, `C066`, `M038`, `M039`, `M040`, `M041` |
| Cross-family posture | IMC `GO`, IoT `READY_FOR_USER_RATIFICATION`, Bio `GO` | `C034`, `C074`, `C081` |
| Open-risk handling | Listed open risks remain visible and non-silent in release notes | `C078`, `C079`, `C080` |

<p>
  <img src=".github/assets/readme/section-bars/compatibility-vector-impact.svg" alt="COMPATIBILITY VECTOR IMPACT" width="100%">
</p>

Compatibility commitments:
- Contract version remains `wave1.0`.
- Compatibility vector SHA256 remains a tracked release artifact.
- Canonical metric authority remains `total_words 844`.

Evidence IDs: `C067`, `C072`, `M059`

<p>
  <img src=".github/assets/readme/section-bars/downstream-action-items.svg" alt="DOWNSTREAM ACTION ITEMS" width="100%">
</p>

Owner decisions required before expanding release automation/process guarantees:
- `Q-REL-001`
- `Q-REL-002`
- `Q-REL-003`
- `Q-REL-004`

*These items represent owner-gated decisions intentionally withheld from public release. They will be published when resolved.*

Until answered, release execution remains manual and evidence-gated.

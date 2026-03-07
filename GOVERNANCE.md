<p>
  <img src=".github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC MASTHEAD" width="100%">
</p>

<p>
  <img src=".github/assets/readme/section-bars/what-this-is.svg" alt="WHAT THIS IS" width="100%">
</p>

This document defines the public governance boundary for evidence handling, status language, and compatibility commitments for ZPE-IMC.

Canonical anchors:
- Repository: `https://github.com/zer0pa/zpe-imc`
- Contact: `architects@zer0pa.ai`

<p>
  <img src=".github/assets/readme/section-bars/evidence-and-claims.svg" alt="EVIDENCE AND CLAIMS" width="100%">
</p>

Governance baseline:
- Technical claims must be evidence-backed; unsupported claims are not treated as release truth.
- Status semantics use explicit taxonomy (`VERIFIED`, `INFERRED`, `UNKNOWN`, `UNVERIFIED`).
- Runtime/state artifacts outrank prose when current operational truth conflicts.
- Contradictions are retained and logged rather than rewritten away.

Evidence IDs: `C001`, `C040`, `C041`, `C042`, `C043`, `C044`, `C045`, `C046`

<p>
  <img src=".github/assets/readme/section-bars/compatibility-commitments.svg" alt="COMPATIBILITY COMMITMENTS" width="100%">
</p>

| Contract coordinate | Current lock | Evidence |
|---|---|---|
| Interface contract version | `wave1.0` | `C067`, `C072` |
| Canonical metric authority | `total_words: 844` | `C067`, `M059` |
| Q-token posture summary | `Q-100..Q-102 READY_FOR_AUTHORITY_PROMOTION`, `Q-103 READY_WITH_LICENSE_BOUNDARY`, `Q-104 VERIFIED` | `C025`, `C055` |
| Tokenizer deployment posture | `INCONCLUSIVE_FOR_DEPLOYMENT` (non-authority) | `C086`, `C087` |

<p>
  <img src=".github/assets/readme/section-bars/summary.svg" alt="STATUS SEMANTICS" width="100%">
</p>

| Token | Meaning |
|---|---|
| `GO_QUALIFIED` | Current evidence supports implemented claims within explicit boundaries. |
| `INCONCLUSIVE` | Evidence conflict remains without deterministic reconciliation. |
| `NO_GO/FAIL` | Core or non-negotiable gates remain unresolved. |
| `PARKED_BY_POLICY` | Scope is intentionally deferred by policy. |

Evidence IDs: `C082`, `C083`, `C084`, `C085`

<p>
  <img src=".github/assets/readme/section-bars/escalation-path.svg" alt="ESCALATION PATH" width="100%">
</p>

Owner decisions required for unresolved governance policy are tracked in the wave owner register:
- `Q-GOV-001`
- `Q-GOV-002`
- `Q-GOV-003`
- `Q-GOV-004`

*These items represent owner-gated decisions intentionally withheld from public release. They will be published when resolved.*

Public-safe withholding rationale:
- Some decisions include active legal sequencing and policy wording that cannot be partially published without creating contradictory guidance.
- Some decisions depend on external partner/timing commitments that are not yet ratified for public release.
- Sanitized outcome summaries will be published after owner ratification closes the dependency chain.

Until these are answered, compatibility and publishability policy remains frozen to the current evidence-backed boundary.

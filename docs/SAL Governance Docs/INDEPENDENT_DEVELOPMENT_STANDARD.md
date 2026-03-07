# LR-03 — Independent Development Evidentiary Standard

**Ref:** O-02 (Critical) | **SAL v6.0 Section:** 4.4.1(d) Rebuttal Mechanism
**Date:** 2026-03-05 | **Status:** RECOMMENDATION

---

## 1. Purpose

Section 4.4.1(d) allows the presumption of derivation to be rebutted through "contemporaneous written documentation" of a "documented independent-development or clean-room process." This document defines what evidence satisfies that standard — both to guide potential challengers **and** to give Zer0pa a clear evidentiary framework for enforcement.

> [!TIP]
> Defining these standards proactively is strategically valuable: it signals legal maturity to acquirers and makes enforcement more predictable. Companies are more likely to pay for a commercial license when the independent-development bar is clearly high.

---

## 2. Minimum Records Required for Independent Development Claim

Any party asserting independent development must produce **all** of the following contemporaneous records:

### 2.1 Personnel Isolation Records

| Record | Requirement |
|--------|------------|
| **Clean-room team roster** | Named list of every individual who participated in the design, architecture, specification, implementation, code review, or testing of the Substantially Similar Implementation |
| **Prior Access declaration** | Signed declaration from each team member confirming they have NOT downloaded, executed, forked, incorporated, or deployed ZPE-IMC software or any derivative thereof |
| **Organizational chart** | Showing separation between clean-room team and any individuals who had Substantive Prior Access |
| **Information barrier memo** | Written policy document establishing the information barrier, distributed to all relevant personnel, dated before development commenced |

### 2.2 Development Provenance Records

| Record | Requirement |
|--------|------------|
| **Design specification** | Architecture and design documents predating any Prior Access, or created after an information barrier was established — must be dated (e.g., via version control timestamps, notarised copies, or legal hold) |
| **Version control log** | Complete commit history of the independent implementation showing incremental development, author attribution, and timestamps |
| **Reference materials log** | List of all external references, prior art, academic papers, and open-source libraries consulted during development — must NOT include ZPE-IMC software, this License, or the Originating Publication |
| **Decision log** | Record of key architectural decisions, including why a directional-primitive approach was chosen and what alternatives were considered |

### 2.3 Pre-Existing Work Evidence (if applicable)

| Record | Requirement |
|--------|------------|
| **Prior art documentation** | If the party claims pre-existing work in directional encoding, they must produce dated artifacts (publications, patents, internal documents) predating 2026-02-24 (date of Originating Publication) |
| **Continuous development timeline** | Showing an unbroken chain of development from pre-existing work to the current implementation — gaps break the chain |

---

## 3. Time Windows

| Event | Window |
|-------|--------|
| **Information barrier establishment** | Must be established *before* any development work on the Substantially Similar Implementation commences |
| **Record creation** | All records must be contemporaneous — created during the development process, not reconstructed after a dispute arises |
| **Record retention** | 5 years from the date of last Substantive Prior Access by any personnel of the claiming party |
| **Audit availability** | Records must be available for review within 30 days of a written request from the Licensor |

---

## 4. Attestation Requirements

### 4.1 Individual Developer Attestation

Each member of the clean-room team must sign an attestation containing:

1. Full name and role in the development project
2. Statement that they have not had Substantive Prior Access (download, execution, forking, incorporation, or deployment of ZPE-IMC)
3. Statement that they have not received any briefing, specification, or description of ZPE-IMC's internal architecture from any person who had Substantive Prior Access
4. Date of attestation
5. Acknowledgement that the attestation may be relied upon in legal proceedings

### 4.2 Corporate Officer Attestation

A senior officer (VP-level or above) of the company must certify:

1. That an information barrier was established and maintained
2. The date the information barrier was established
3. That the company's compliance function monitored the barrier
4. That no breach of the barrier was identified during the development period

---

## 5. Audit Threshold

The Licensor may request an independent audit of the independent-development records if **any two** of the following conditions are met:

1. The party had at least one individual with confirmed Substantive Prior Access
2. The Substantially Similar Implementation uses a directional-primitive approach with N ≥ 2
3. The Substantially Similar Implementation was developed within 24 months of confirmed Substantive Prior Access
4. The party's product competes with ZPE-IMC in the same market segment
5. The party's Annual Gross Revenue exceeds the Revenue Threshold ($10M)

**Audit scope:** Limited to the records specified in Section 2 above. The audit shall be conducted by a mutually agreed independent auditor, at the Licensor's cost initially. If the audit finds material deficiencies in the independent-development records, the audited party bears the reasonable cost.

---

## 6. What Does NOT Satisfy the Standard

The following are **insufficient** to rebut the presumption, standing alone:

- General corporate assertions of independent development without contemporaneous documentation
- After-the-fact reconstruction of a development timeline
- Code comparison showing syntactic differences (the Functional Equivalence Test governs, not code similarity)
- A claim that the approach is "obvious" or "well-known" without specific cited prior art predating the Originating Publication
- Employee testimony unsupported by contemporaneous documentation
- The existence of parallel prior art in the field (relevant to enforceability of the underlying IP, but not to the contractual presumption under this License)

---

## 7. Strategic Notes for Zer0pa

> [!IMPORTANT]
> Publishing this standard openly in the license repository serves three purposes:
> 1. **Deters casual copying** — the bar is clearly high enough that paying for a commercial license is easier
> 2. **Signals legal maturity** — acquirers see a well-defined enforcement framework, not ad-hoc litigation risk
> 3. **Provides fair notice** — strengthens enforceability by demonstrating the parties knew the standard in advance

---

*LR-03 — Prepared as legal analysis, not formal legal advice. Recommend review by IP counsel.*

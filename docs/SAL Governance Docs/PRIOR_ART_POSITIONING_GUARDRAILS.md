# LR-10 — Prior-Art Strategy Legal Boundaries

**Ref:** O-06 (Medium) | **SAL v6.0 Section:** 5 (Defensive Publication / Prior-Art Acknowledgement)
**Date:** 2026-03-05 | **Status:** GUARDRAILS

---

## 1. Purpose

The SAL v6.0 explicitly positions the Originating Publication as prior art to block third-party patents. This document defines what Zer0pa can safely claim publicly versus what must remain legally qualified.

---

## 2. What Is Prior Art (and What It Does)

Prior art, in patent law, is any public disclosure of an invention before a patent application's filing date. By publicly disclosing the ZPE architecture, Zer0pa creates a record that patent examiners can cite to reject future patent applications that cover the same concepts.

**This is a legitimate and well-recognized strategy.** Companies from IBM to Tesla have used defensive publications to protect freedom-to-operate.

---

## 3. What CAN Be Claimed Publicly

### ✅ Safe Statements

| Statement | Notes |
|-----------|-------|
| "The Originating Publication is a defensive disclosure establishing Zer0pa's priority of disclosure" | Factual — mirrors Section 5 language |
| "The ZPE architecture, including Compass-8 and the N-primitive family, was first publicly disclosed by Zer0pa on [date]" | Factual — date-anchored |
| "This disclosure is intended to constitute prior art for purposes of assessing novelty and patentability of similar systems" | Factual legal intent — directly from Section 5 |
| "The disclosure covers the full scope of applications described in the Originating Publication, including [list of domains]" | Factual — describes the content of the disclosure |
| "We encourage the community to use this work freely under the SAL v6.0 license terms" | Promotional — accurate |

### ✅ Safe FAQ/README Language

> "ZPE-IMC was publicly disclosed on 24 February 2026 as a defensive disclosure and prior-art record. This disclosure is intended to establish Zer0pa's priority of invention and to serve as prior art against subsequent patent claims in the field of directional-primitive multimodal encoding."

---

## 4. What MUST Remain Legally Qualified

### ⚠️ Statements Requiring Qualification

| Statement | Risk | Qualified Alternative |
|-----------|------|----------------------|
| "No one can patent this" | **Overstatement** — prior art doesn't guarantee patent rejection; it's one factor examiners consider | "This disclosure is intended to serve as prior art that patent examiners may cite when evaluating subsequent applications" |
| "We have killed the patentability of this entire field" | **Overstatement** — prior art can be designed around | "We believe this disclosure covers the core concepts of N-primitive directional encoding for multimodal data" |
| "Any patent in this space is invalid because of our disclosure" | **False** — existing patents predating the disclosure are unaffected, and future patents may cover novel improvements | "This disclosure is intended to be considered in assessing novelty of future patent applications covering the Protected Architecture" |
| "ZPE is the first system to do X" | **Unverifiable** — chain codes, geometric quantization, and related approaches predate ZPE | "ZPE is, to the Licensor's knowledge, the first publicly disclosed system combining N-primitive directional encoding with unified multimodal transport" |

### ❌ Prohibited Statements

| Statement | Why |
|-----------|-----|
| "We own the patent on directional encoding" | **False** — no patent has been filed or granted |
| "Anyone who builds something similar infringes our patent" | **False** — there is no Zer0pa patent; the License creates contractual obligations, not patent rights |
| "Our prior art makes it illegal to build a competing system" | **False** — prior art affects patentability, not legality of development |
| "The entire field of multimodal encoding is our prior art" | **Gross overstatement** — prior art scope is limited to what was actually disclosed |

---

## 5. Distinction: Contractual vs. IP Rights

| Right Type | Mechanism | Scope |
|-----------|-----------|-------|
| **Contractual** (License) | Section 4.4 — parties who accept the license are bound by the Functional Equivalence Test and Prior Access presumption | Limited to parties who accepted the license |
| **Defensive publication** (Prior art) | Section 5 — disclosure intended to block third-party patents | Affects patentability globally, but does not create enforceable rights against non-licensees |
| **Copyright** | Standard copyright protection over the code and documentation | Protects expression, not ideas or architecture |
| **Trademark** | "Zer0pa," "ZPE," "Compass-8" — registered or common-law marks | Protects brand identity, not functional concepts |

> [!WARNING]
> Public statements must not conflate these mechanisms. Saying "our license prevents anyone from building a similar system" is inaccurate — the license binds licensees contractually; the prior art affects patentability; neither creates a blanket prohibition on independent development.

---

## 6. Recommended Public Positioning

### For README / FAQ

> **Intellectual Property:**
> ZPE-IMC is released under the Zer0pa Source-Available License v6.0 (SAL v6.0). The associated Originating Publication serves as a defensive disclosure and prior-art record, intended to establish Zer0pa's priority of invention in the field of N-primitive directional encoding for multimodal information transport. This disclosure is intended to be considered by patent examiners when evaluating the novelty of subsequent applications. The SAL v6.0 license defines the terms under which the software and Protected Architecture may be used. See LICENSE for full terms.

### For Investor / Acquirer Presentations

> **IP Strategy:**
> Zer0pa employs a three-layer IP protection strategy: (1) contractual protection via the SAL v6.0 license, which binds users to commercial licensing terms above $10M revenue; (2) defensive publication establishing prior art across the full scope of the N-primitive encoding family; and (3) trademark protection for the ZPE, Zer0pa, and Compass-8 marks. This strategy is designed to maximize freedom-to-operate while creating strong commercial leverage against enterprise adopters.

---

*LR-10 — Prepared as legal analysis, not formal legal advice. Recommend review by IP counsel and communications team.*

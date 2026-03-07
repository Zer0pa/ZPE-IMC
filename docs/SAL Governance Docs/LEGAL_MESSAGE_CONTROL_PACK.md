# LR-12 — External Legal Messaging Control Pack

**Ref:** Cross-cutting | **SAL v6.0 All Sections**
**Date:** 2026-03-05 | **Status:** CANONICAL MESSAGING — For README/FAQ/Support

---

## 1. Purpose

Create approved short-form legal statements for use in public-facing documents (README, FAQ, CONTRIBUTING, SECURITY, website). Eliminates the risk of accidental overstatement or understatement. All public legal references should draw from this pack.

---

## 2. Canonical Short-Form Statements

### 2.1 License Summary (for README)

> **License:** ZPE-IMC is released under the [Zer0pa Source-Available License v6.0](https://github.com/Zer0pa/ZPE-License-Commercial) (SAL v6.0). This is a source-available license with delayed open-source conversion — **not** an open-source license.
>
> **Free use for:** individuals, researchers, academic institutions, non-profits, open-source projects, and organisations with annual gross revenue below the Revenue Threshold.
>
> **Commercial license required for:** organisations exceeding the Revenue Threshold that use ZPE-IMC in production, hosted services, AI training, or embedded/OEM distribution. Contact architects@zer0pa.ai.

### 2.2 License Type Clarification

> ZPE-IMC is licensed under a **source-available** license (SAL v6.0). It is **not** open-source as defined by the Open Source Initiative (OSI). The source code is publicly available for inspection, evaluation, research, and non-commercial use. Commercial production use by entities above the Revenue Threshold requires a separate Commercial License.

### 2.3 Revenue Threshold Statement

> The SAL v6.0 Revenue Threshold is USD $10,000,000 in Annual Gross Revenue (consolidated). Individuals and organisations below this threshold may use ZPE-IMC freely for any purpose, including commercial use. Organisations exceeding the threshold must obtain a Commercial License for Production Use.

> [!NOTE]
> If you adopt the LR-11 recommendation to raise the threshold to $100M, update this to: "USD $100,000,000 in Annual Gross Revenue (consolidated)."

### 2.4 Conversion Statement

> Each version of ZPE-IMC automatically becomes available under the Apache License 2.0 on its Change Date (the date specified in the release metadata for that version). After conversion, community users receive the code under Apache 2.0. Parties who previously accepted the SAL v6.0 remain bound by certain surviving obligations as specified in the license.

### 2.5 Prior Art / IP Statement

> The ZPE architecture was first publicly disclosed as a defensive disclosure and prior-art record. This disclosure is intended to establish Zer0pa's priority of invention in the field of N-primitive directional encoding for multimodal information transport. The disclosure is intended to be considered by patent examiners when evaluating the novelty of subsequent patent applications.

### 2.6 AI Training Statement

> Use of ZPE-IMC as training data, fine-tuning data, evaluation data, benchmark data, tokenisation vocabulary, or encoding substrate for any AI system is subject to the same terms as Production Use if conducted by or on behalf of an entity exceeding the Revenue Threshold. Such use must be disclosed in the AI system's model card or documentation.

### 2.7 Contribution Statement (for CONTRIBUTING.md)

> By submitting a contribution, you grant Zer0pa a perpetual, worldwide, non-exclusive, royalty-free, irrevocable license to use, modify, distribute, sublicense, and commercially exploit your contribution as part of ZPE-IMC. You retain copyright. Your contribution is distributed under the SAL v6.0 license. See the full license for details.

### 2.8 Security Contact Statement (for SECURITY.md)

> ZPE-IMC is licensed under the Zer0pa Source-Available License v6.0. Security vulnerabilities should be reported to architects@zer0pa.ai. The license version governing this release is SAL v6.0.

---

## 3. Prohibited Phrasing

The following phrasings **must not** appear in any Zer0pa public-facing material:

| ❌ Prohibited | Why | ✅ Use Instead |
|--------------|-----|---------------|
| "Open-source license" | SAL v6.0 is NOT OSI-approved | "Source-available license" |
| "Apache-2.0" in pyproject.toml or CITATION.cff | Material misrepresentation | `LicenseRef-Zer0pa-SAL-6.0` |
| "Free for all use" | Inaccurate — Production Use above threshold requires license | "Free for individuals, researchers, and organisations below the Revenue Threshold" |
| "No one can patent this" | Overstatement (see LR-10) | "This disclosure is intended to serve as prior art" |
| "We own the patent" | No patent exists | Do not reference patents as held rights |
| "This code is in the public domain" | It is not — it is copyrighted and licensed | "This code is available under the SAL v6.0 license" |
| "Licensed under SAL v5.1" (in any document) | Outdated — creates legal inconsistency (see R-01) | "Licensed under SAL v6.0" |
| "Licensed under Apache-2.0" (before Change Date) | False until Change Date passes | "Will convert to Apache 2.0 on [Change Date]" |
| "Any similar system infringes our rights" | Overstatement — license creates contractual, not patent, rights | "Systems within the scope of the Protected Architecture are subject to the SAL v6.0 license terms if the developer has accepted this License" |
| "Our AI clause legally binds all AI agents" | Overstatement — agents lack legal capacity | "The deploying entity is responsible for AI agent compliance with this License" |

---

## 4. Version Consistency Checklist

> [!CAUTION]
> The red team reports identified that 5+ documents reference SAL v5.1 while the actual license is v6.0. Before publishing any update, run this checklist:

- [ ] `LICENSE` → SAL v6.0 ✅
- [ ] `CITATION.cff` → `LicenseRef-Zer0pa-SAL-6.0` (NOT `Apache-2.0`, NOT `SAL-5.1`)
- [ ] `pyproject.toml` → `LicenseRef-Zer0pa-SAL-6.0` (NOT `Apache-2.0`)
- [ ] `FAQ.md` → All references → SAL v6.0
- [ ] `SECURITY.md` → All references → SAL v6.0
- [ ] `CONTRIBUTING.md` → All references → SAL v6.0
- [ ] `README.md` → License section → SAL v6.0
- [ ] `__init__.py` version matches `CITATION.cff` and `CHANGELOG.md`

---

## 5. Template: Response to "What License Is This?"

For support inquiries or FAQ:

> ZPE-IMC is released under the Zer0pa Source-Available License v6.0 (SAL v6.0). This is a source-available license — not an open-source license as defined by the OSI. The source code is publicly available for inspection, study, and non-commercial use. Organisations with annual gross revenue above the Revenue Threshold (currently $10M USD) that wish to use ZPE-IMC in production must obtain a Commercial License. Each version of the software automatically converts to Apache 2.0 on its Change Date. Full license text: https://github.com/Zer0pa/ZPE-License-Commercial

---

## 6. Template: Response to "Can I Use This for AI Training?"

> Use of ZPE-IMC as training data, fine-tuning data, or evaluation data is governed by the SAL v6.0 license. If your organisation's annual gross revenue exceeds the Revenue Threshold, such use requires a Commercial License. All AI training use must be disclosed in the model card or equivalent documentation. Contact architects@zer0pa.ai for commercial licensing inquiries.

---

*LR-12 — Prepared as communications/legal guidance, not formal legal advice. Recommend review by IP counsel and communications team.*

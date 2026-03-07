# LR-11 — Revenue Threshold Transition Policy

**Ref:** O-07 (Medium) | **SAL v6.0 Sections:** 1 (Revenue Threshold), 4.2, 4.3
**Date:** 2026-03-05 | **Status:** RECOMMENDATION

---

## 1. Strategic Context

**Your goal:** Catch big fish ($100M+), let everyone else swim freely, and don't build a complex account management operation.

The current SAL v6.0 sets the Revenue Threshold at **$10M Annual Gross Revenue**. This means any entity crossing $10M must obtain a Commercial License. But the license is silent on:
- What happens **during** the crossing (mid-year)
- Whether there is a **grace period**
- Whether obligations are **retroactive**
- What triggers the **enforcement start**

This policy addresses all four.

---

## 2. Revenue Threshold — Should It Be $10M or $100M?

> [!IMPORTANT]
> **Strong recommendation: Raise the Revenue Threshold from $10M to $100M.**

### Rationale

| Factor | $10M Threshold | $100M Threshold |
|--------|---------------|-----------------|
| **Number of potential licensees** | Hundreds (every mid-stage startup) | Tens (only genuine enterprises) |
| **Account management burden** | High — many small deals to manage | Low — few, large deals |
| **Revenue per deal** | Small ($10K-$50K per customer?) | Large ($250K-$1M+ per customer) |
| **Community adoption** | Chilled — startups worry about hitting $10M | Maximized — virtually all developers and startups are free |
| **Acquisition attractiveness** | Lower — enterprise buyer sees complex licensing compliance | Higher — clean, enterprise-only commercial model |
| **Competitive positioning** | Looks greedy — even seed-stage SaaS companies may cross $10M | Looks generous — "we only charge the Googles and Metas" |
| **Strategic alignment** | Doesn't match stated goal of "large-ticket only" | **Perfectly aligned** |

### Additional Consideration: $100M Matches Your Target

You explicitly said you're targeting **$100M+ companies.** Setting the threshold at $10M creates a messy middle zone: companies between $10M and $100M that are too small to be strategic customers but big enough to trigger the commercial requirement. These companies will be a compliance burden, not revenue sources.

**With a $100M threshold:**
- Startups build on ZPE freely → ecosystem grows → technology becomes standard
- When they get acquired by a $100M+ company or grow to $100M themselves, they buy a license
- You only manage a handful of high-value enterprise accounts

---

## 3. Transition Treatment

### 3.1 When Does the Obligation Trigger?

**Recommended: At the end of the first fiscal year in which Annual Gross Revenue exceeds the Revenue Threshold.**

| Current | Proposed |
|---------|----------|
| Obligation seems to apply from the *moment* revenue exceeds threshold | Obligation triggers at fiscal year-end, measured on prior FY revenue |

**Reasoning:** Annual Gross Revenue is a backwards-looking metric. You cannot know you've crossed $100M until the fiscal year closes. Triggering the obligation mid-year creates an impossible compliance situation.

### 3.2 Grace Period

**Recommended: 180-day grace period from the end of the FY in which the threshold was exceeded.**

```
FY End (revenue exceeded) ───── 180 days ─────── Commercial License required
                                       ↑
                               Grace period: can continue  
                               under SAL v6.0 while  
                               negotiating Commercial License
```

**During the grace period:**
- The entity may continue all existing use under SAL v6.0
- The entity must initiate Commercial License discussions with Zer0pa within 60 days of FY-end
- New deployments or new Hosted Services during the grace period are permitted but become retroactively subject to the Commercial License once executed

### 3.3 Notification Duty

**Recommended: Mutual notification duty.**

| Party | Obligation |
|-------|-----------|
| **Licensee** | Must notify Zer0pa within 60 days of the FY-end in which their Annual Gross Revenue exceeded the Revenue Threshold |
| **Zer0pa** | Must provide a written response within 30 days of receiving notification, including preliminary Commercial License terms |

### 3.4 Retroactivity

**Recommended: NO retroactive obligations.**

| Current | Proposed |
|---------|----------|
| Ambiguous — could be read as requiring retroactive commercial licensing | Explicit: "Use prior to the grace period expiry is governed by the SAL v6.0 source-available terms. Commercial License terms apply prospectively from the date of license execution." |

**Reasoning:** Retroactive obligations are hostile to adoption and potentially unenforceable. A growing startup should not face back-dated licensing fees for years of pre-threshold use. Prospective-only treatment encourages adoption.

### 3.5 Enforcement Start

**Recommended: Enforcement begins after the grace period expires.**

If a party:
1. Exceeds the Revenue Threshold, AND
2. Fails to initiate Commercial License discussions within 60 days, AND
3. Fails to execute a Commercial License within the 180-day grace period

Then: their SAL v6.0 license is deemed to not permit Production Use (per Section 4.2), and standard termination provisions apply (Section 11).

---

## 4. Proposed License Amendment

Add the following as new Section 4.3.5:

```
4.3.5 Revenue Threshold Transition. If Your Annual Gross Revenue exceeds
the Revenue Threshold for the first time (measured as of the end of Your
fiscal year), You must initiate Commercial License discussions with the
Licensor within sixty (60) days of the end of that fiscal year. You may
continue use under this License for a period of one hundred eighty (180)
days from the end of that fiscal year (the "Transition Period") while
Commercial License terms are negotiated in good faith. If You do not
execute a Commercial License by the end of the Transition Period, Your
Production Use is subject to Section 4.2 and applicable termination
provisions. Use of the Software prior to the end of the Transition Period
is governed by this License and is not retroactively subject to the
Commercial License.
```

---

## 5. Revenue Bracket Strategy (Commercial License Pricing)

For your commercial licensing desk (not in the license text, but in your sales playbook):

| Revenue Bracket | License Model | Suggested Range |
|----------------|---------------|-----------------|
| $100M — $500M | Annual subscription | $250K — $500K/yr |
| $500M — $1B | Annual subscription + support | $500K — $1M/yr |
| $1B — $10B | Enterprise license + indemnification | $1M — $5M/yr |
| $10B+ | Strategic partnership / acquisition discussion | Custom |

> [!TIP]
> This tiered approach means you're only managing 10-20 accounts at any time — exactly what you want. Each account is large enough to justify white-glove service and legal attention.

---

## 6. Decision Summary

| Item | Current | Recommended |
|------|---------|------------|
| Revenue Threshold | $10M | **$100M** |
| Trigger point | Ambiguous | End of fiscal year |
| Grace period | None specified | **180 days** |
| Notification duty | Licensee only (4.3.1) | **Mutual** |
| Retroactivity | Ambiguous | **Prospective only** |
| Enforcement start | Immediate | **After grace period** |

---

*LR-11 — Prepared as legal analysis, not formal legal advice. Recommend review by IP counsel and commercial strategy team.*

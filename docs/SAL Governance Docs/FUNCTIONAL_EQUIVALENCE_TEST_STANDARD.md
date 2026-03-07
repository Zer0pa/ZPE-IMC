# LR-08 — Functional Equivalence Test Standard

**Ref:** O-08 (Medium) | **SAL v6.0 Section:** 1 (Definitions — "Substantially Similar Implementation")
**Date:** 2026-03-05 | **Status:** RECOMMENDATION

---

## 1. Purpose

Section 1 defines the three-part "Functional Equivalence Test" for determining whether a system is a Substantially Similar Implementation. This document operationalizes that test into a defensible, repeatable legal-technical standard.

---

## 2. Current Three-Part Test (Section 1)

A system is Substantially Similar if it satisfies **all three** of:

| Prong | Test |
|-------|------|
| **1. Purpose equivalence** | The system encodes, compresses, routes, or reconstructs multimodal information |
| **2. Mechanism equivalence** | The system uses a finite set of directional, orientational, or geometric primitives as its fundamental encoding vocabulary |
| **3. Architecture equivalence** | The system uses a shared primitive basis and a unified transport mechanism across multiple modality types |

---

## 3. Operationalized Criteria

### Prong 1: Purpose Equivalence

**Question:** Does the system handle information across more than one modality using a unified encoding scheme?

| Criterion | Threshold |
|-----------|-----------|
| Number of modalities | ≥ 2 distinct modality types (e.g., text + image, audio + video) |
| Operation type | Any of: encode, compress, transcode, tokenize, transmit, store, or reconstruct |
| Unified scheme | A single encoding vocabulary or transport format is used across modalities (not modality-specific codecs chained together) |

**NOT triggered by:**
- Single-modality codecs (e.g., a pure image encoder)
- Modality-specific encoders that output to a common container format (e.g., separate JPEG + MP3 in an MP4 container)
- Multimodal systems that use separate, independent encoding pipelines with no shared primitive vocabulary

### Prong 2: Mechanism Equivalence

**Question:** Does the system use a finite set of geometric, directional, or orientational primitives as the core encoding unit?

| Criterion | Threshold |
|-----------|-----------|
| Primitive type | Directional (compass-like), orientational (rotation/angle-based), or geometric (lattice/grid-based) — whether explicit or learned |
| Finite vocabulary | A bounded set of N ≥ 2 primitives (not a continuous vector space unless it is discretized into a finite codebook) |
| Encoding role | Primitives must be the **fundamental** encoding vocabulary, not a secondary feature. The information must be represented *as* primitive sequences, not merely *mapped through* a layer |

**NOT triggered by:**
- Continuous embedding spaces (e.g., CLIP, BERT) — unless discretized into a finite directional codebook
- Standard VQ-VAE where the codebook entries are learned embeddings without directional/geometric semantic grounding
- Attention mechanisms (despite geometric interpretability, attention heads are not a "finite encoding vocabulary")
- Traditional chain codes used solely for contour encoding in single-modality image processing

### Prong 3: Architecture Equivalence

**Question:** Does the system share a single primitive basis across modality types via a unified transport mechanism?

| Criterion | Threshold |
|-----------|-----------|
| Shared basis | The same primitive vocabulary (or profile variants thereof) is used for encoding across modalities |
| Unified transport | A single packet, word, frame, or envelope structure routes encoded data across modality types |
| Routing mechanism | Type bits, mode fields, lane identifiers, or functionally equivalent routing logic dispatches primitives to modality-specific decoders |

**NOT triggered by:**
- Systems that use different codebooks for different modalities
- Container formats that wrap modality-specific encodings
- Feature fusion systems that combine embeddings from separate encoders

---

## 4. Burden Allocation

| Scenario | Burden |
|----------|--------|
| Party had Substantive Prior Access | **Defendant** must prove independent development (per LR-02/LR-03) |
| Party had no Prior Access | **Licensor** must prove equivalence under all three prongs |
| Dispute over whether Prior Access occurred | **Licensor** must prove Substantive Prior Access occurred |

---

## 5. Evidentiary Thresholds

To establish that a system satisfies a given prong, the asserting party must provide:

| Evidence Type | Standard |
|--------------|----------|
| **Purpose equivalence** | Documentation, marketing materials, technical specifications, or code analysis showing multimodal encoding |
| **Mechanism equivalence** | Code analysis, architectural documentation, or expert analysis demonstrating finite directional/geometric primitive vocabulary |
| **Architecture equivalence** | Transport protocol analysis, packet/word format documentation, or code analysis showing shared basis + unified routing |

**Expert analysis:** Either party may retain a qualified technical expert (software architect or information theory specialist) to provide an opinion on equivalence. The expert must apply the criteria in this document.

---

## 6. Safe Harbor Examples

The following systems are **explicitly NOT** Substantially Similar Implementations (absent additional factors):

| System | Reason |
|--------|--------|
| CLIP / BERT / GPT embeddings | Continuous vector space, not finite directional primitives |
| Standard VQ-VAE | Learned codebook without directional/geometric grounding |
| WebP / AVIF / H.265 | Single-modality codecs |
| Multimodal transformers (Gemini, GPT-4V) | Separate tokenizers per modality, not shared primitive vocabulary |
| Freeman chain codes for image contours | Single-modality; historical prior art |
| Standard BPE tokenizers | Text-only; not multimodal transport |

---

## 7. Grey-Zone Examples (Require Case-by-Case Assessment)

| System | Why It's Grey |
|--------|--------------|
| A multimodal tokenizer using learned geometric codebook | Depends on whether primitives are directional/geometric |
| A system using 4 directional primitives for state-machine encoding across 2 modalities | Likely equivalent if all three prongs met |
| An embedding space that discretizes into 8 directions per layer | Depends on whether the directions are the fundamental encoding unit or a secondary feature |

---

## 8. Strategic Notes

> [!TIP]
> Publishing clear safe-harbor examples reduces the "chilling effect" that the red team reports identified. By saying explicitly "CLIP and VQ-VAE are not covered," you:
> 1. Remove the strongest objection corporate lawyers will raise
> 2. Make the scope defensible (you're not claiming all of representation learning)
> 3. Make the license more attractive for community adoption
> 4. Sharpen enforcement against genuine copycats

---

*LR-08 — Prepared as legal-technical analysis, not formal legal advice. Recommend review by IP counsel and a technical expert.*

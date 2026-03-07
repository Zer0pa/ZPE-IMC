<p>
  <img src="../../.github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

Contract Version: `wave1.0`
Package: `zpe-multimodal==3.0.0`
Scope Root: `<repo-root>`

<p>
  <img src="../../.github/assets/readme/section-bars/purpose.svg" alt="PURPOSE" width="100%">
</p>
This contract freezes the IMC multimodal stream invariants consumed by downstream Bio/IoT lanes without requiring direct runtime imports from IMC.

<p>
  <img src="../../.github/assets/readme/section-bars/word-layout.svg" alt="WORD LAYOUT" width="100%">
</p>
- Total bits per word: `20`
- Mode bits: `[19:18]`
- Version bits: `[17:16]`
- Payload bits: `[15:0]`
- Payload mask: `0xFFFF`

<p>
  <img src="../../.github/assets/readme/section-bars/mode-semantics.svg" alt="MODE SEMANTICS" width="100%">
</p>
- `mode=0` (`NORMAL`): text unit words.
- `mode=1` (`ESCAPE`): escaped UTF-8 bytes.
- `mode=2` (`EXTENSION`): modality extension payloads.
- `mode=3` (`RESERVED`): currently legal for mental control words only.

<p>
  <img src="../../.github/assets/readme/section-bars/modality-markers.svg" alt="MODALITY MARKERS" width="100%">
</p>
- `diagram`: `0x8000`
- `music`: `0x4000`
- `voice`: `0x2000`
- `bpe`: `0x1000`
- `touch`: `0x0800` (non-image payloads)
- `image family`: mask `0x0C00`, enhanced value `0x0400`
- `smell`: `0x0200` (non-image payloads)
- `mental`: `0x0100`
- `taste`: `0x0400` (versioned disambiguation on v1/v2/v3)

<p>
  <img src="../../.github/assets/readme/section-bars/dispatch-precedence.svg" alt="DISPATCH PRECEDENCE" width="100%">
</p>
1. mental (reserved-mode words)
2. music
3. voice
4. diagram
5. bpe
6. taste (extension words with v1/v2/v3 + taste bit)
7. touch (non-image payloads)
8. smell (non-image payloads)
9. mental (extension non-image payloads)
10. image family
11. text fallback

<p>
  <img src="../../.github/assets/readme/section-bars/canonical-runtime-context-wave-1.svg" alt="CANONICAL RUNTIME CONTEXT (WAVE-1)" width="100%">
</p>
- `make test`: `PASS`
- `make demo`: `PASS`
- `make comet-run` (local fallback): `PASS`
- `python -m pytest tests tests_phase3 -q`: `PASS`
- Canonical demo stream (`executable/demo.py`): `total_words=844`
- Canonical modality counts:
  - `text=52`, `diagram=133`, `music=42`, `voice=70`, `image=498`, `bpe=3`, `mental=7`, `touch=4`, `smell=6`, `taste=29`

<p>
  <img src="../../.github/assets/readme/section-bars/compatibility-commitments.svg" alt="COMPATIBILITY COMMITMENTS" width="100%">
</p>
- IMC keeps backward decode compatibility for prior wave streams unless a documented breaking policy exception is approved.
- Changes that alter modality markers, word layout, or dispatch precedence require contract version increment and downstream replay.
- Bio/IoT consume this contract via static artifacts (`IMC_COMPATIBILITY_VECTOR.json`) rather than runtime imports.

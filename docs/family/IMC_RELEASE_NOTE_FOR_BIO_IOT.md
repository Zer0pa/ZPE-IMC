<p>
  <img src="../../.github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

Release Wave: `Wave-1`
IMC Package: `zpe-multimodal==3.0.0`
Contract Vector: `docs/family/IMC_COMPATIBILITY_VECTOR.json`

<p>
  <img src="../../.github/assets/readme/section-bars/what-changed-in-wave-1.svg" alt="WHAT CHANGED IN WAVE-1" width="100%">
</p>
1. Release isolation hardened for scoped `v0.0` execution.
2. Package CLI added: `zpe-imc` with `info`, `validate`, `demo` JSON surfaces.
3. Quality gate expansion added malformed-stream fuzz and determinism replay tests.
4. CI/release workflows added under `.github/workflows`.
5. Compatibility contract artifacts frozen for downstream ingestion.

<p>
  <img src="../../.github/assets/readme/section-bars/downstream-action-items.svg" alt="DOWNSTREAM ACTION ITEMS" width="100%">
</p>
1. Bio owner: import and pin `IMC_COMPATIBILITY_VECTOR.json` in Bio integration tests.
2. IoT owner: replay stream-compat tests against canonical metrics (`total_words=844`, frozen counts).
3. Platform owner: configure required checks to match `imc-ci` and `imc-release` workflow jobs.

<p>
  <img src="../../.github/assets/readme/section-bars/no-change-guarantees.svg" alt="NO-CHANGE GUARANTEES" width="100%">
</p>
1. IMC word layout and modality marker contract is unchanged from runtime behavior in this release.
2. Core modality semantics remain deterministic under current gate suite.
3. BPE remains optional adaptor semantics (not promoted to mandatory core tokenization path).

<p>
  <img src="../../.github/assets/readme/section-bars/escalation-path.svg" alt="ESCALATION PATH" width="100%">
</p>
If downstream replay diverges from the compatibility vector, open an IMC contract issue and attach:
1. failing stream fixture,
2. observed counts,
3. expected counts from compatibility vector,
4. exact replay command.

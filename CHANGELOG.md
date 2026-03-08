<p>
  <img src=".github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

All notable public release-surface changes to ZPE-IMC are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This changelog tracks the public release surface only. No tagged public
release is published yet. Component-local versions in `code/` remain
internal package/runtime metadata until the first public release tag is
issued.

---

<p>
  <img src=".github/assets/readme/section-bars/unreleased.svg" alt="[UNRELEASED]" width="100%">
</p>
### Unreleased

Pre-release legal/package normalization landing.

### Added

- `docs/LEGAL_BOUNDARIES.md` as the compact public note for package
  authority plus smell/taste release boundaries

### Changed

- README and ARCHITECTURE now surface the three current authority
  dimensions explicitly: integrated modality transport, Rust-enhanced
  runtime proof, and provenance/custody discipline
- README runtime wording now states throughput in
  `imc_stream_words/sec` transport words rather than natural-language
  words/sec
- Tokenizer references were removed from outward/current-facing release
  surfaces
- Non-license publication/locator hedges were removed from outward
  release-facing docs and citation surfaces
- README and FAQ front-door wording now present the repo as a curated
  authority snapshot ahead of the first tagged public release, rather
  than as live packaged release guidance
- Active acquisition/reporting links now point to the provisioned
  external auditor snapshot surface instead of the earlier dead
  front-door repo path
- Root `LICENSE` authority is now carried consistently across the
  Python, native Rust, and WASM package surfaces
- Native Rust and WASM package manifests no longer advertise Apache
  2.0 and now point back to the repository root `LICENSE`
- Cargo and npm publication are disabled for the native/runtime and
  WASM package surfaces until any future owner-directed packaging pass
- Repository citation now cites the software record directly and avoids
  invented external locators

---

<!-- versions -->
[Unreleased]: https://github.com/Zer0pa/ZPE-IMC.git

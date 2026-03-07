# Legal Boundaries

This note is a release-surface summary only. [LICENSE](../LICENSE) at the repository root is the legal source of truth for Zer0pa Source-Available License v6.0 (SAL v6.0).

## Package Surfaces

- `code/pyproject.toml` is governed by the root `LICENSE`.
- `code/rust/imc_kernel/Cargo.toml` and `code/rust/wasm_codec/Cargo.toml` are internal component crates under the root `LICENSE`; crate publication is disabled.
- `code/wasm/package.json` and `code/wasm/pkg/package.json` are private package surfaces and are not independently published.
- Component-local versions in `code/` are internal package/runtime metadata until the first tagged public release is issued.

## Smell

Current public authority is limited to the active subset `SmellNet_HF + OpenPOM_GS_LF`. Direct `SmellNet_GitHub_Direct` is excluded. Treat smell as `READY_WITH_LICENSE_BOUNDARY`, not as fully open.

## Taste

Current public authority is limited to the commercial-safe stack already reflected in the repo. Keep these caveats attached: `0x0400` overlap, derived-evidence history, portability defect, and `ChemTastesDB` commercial exclusion.

<p>
  <img src="../../.github/assets/readme/zpe-masthead.gif" alt="ZPE-IMC Masthead" width="100%">
</p>

# zpe-multimodal

ZPE Integrated Modality Codec (IMC) Python package.

The package exposes:

- Unified stream API: `IMCEncoder`, `IMCDecoder`, `stream_summary`, `stream_to_json`, `json_to_stream`.
- CLI entrypoint: `zpe-imc`.
- Text compatibility surface: the top-level `encode` / `decode` helpers
  plus the class-based parity API. These remain available for text-parity
  and adapter compatibility but are not the governing outward authority
  claim for the repository.

Current authority for this package follows the repo-wide three-dimensional
story: integrated modality transport, a Rust-backed deterministic runtime,
and provenance/custody discipline around the accepted path.

External acquisition is handled at the repo root. This package README
assumes the repository has already been obtained through the provisioned
auditor/contributor clone surface documented in `../README.md`.

---

<p>
  <img src="../../.github/assets/readme/section-bars/install.svg" alt="INSTALL" width="100%">
</p>

```bash
pip install zpe-multimodal
```

Editable install for local development:

```bash
pip install -e ".[dev]"
```

Repo-local operator path for the accepted Rust-backed runtime, from the
repository root and using the repo venv explicitly:

```bash
./.venv/bin/python -m pip install -e "./code[full,bench,dev]"
./code/rust/imc_kernel/build_install.sh
./.venv/bin/python - <<'PY'
from zpe_multimodal.core.imc import get_kernel_backend_info
print(get_kernel_backend_info())
PY
./.venv/bin/python -m pytest ./code/tests/test_imc_rust_kernel_native.py -q
./.venv/bin/python ./executable/run_with_comet.py
```

Expected backend facts:
- `backend='rust'`
- `compiled_extension=True`
- `fallback_used=False`
- `payload_layout='u32le_bytes+spans_v1'`
- `ffi_contract_version='imc_flat_u32le_v1'`

Current accepted run facts:
- `run_name='IMC-Canonical-20260307T225939Z'`
- `benchmark_run_id='A4-BENCH-20260307T230025Z'`
- `tests_passed=170`
- `canonical_total_words_per_sec=286165.1102`

The older `wave1.0` / `total_words=844` demo value remains frozen contract
and historical demo truth only. It is not the package/runtime authority path.

Release-default runtime proof path:
- `./executable/run_with_comet.py` runs in local-only proof mode by default and does not require Comet or Opik credentials.
- Internal live observability remains available via:
  `COMET_API_KEY=... OPIK_API_KEY=... ./.venv/bin/python ./executable/run_with_comet.py --enable-classic-comet --enable-opik`

If `compiled_extension` is false or `fallback_used` is true, stop. That is not
the accepted run-of-record path.

---

<p>
  <img src="../../.github/assets/readme/section-bars/quick-start.svg" alt="QUICK START" width="100%">
</p>

This snippet exercises the retained text compatibility surface. Use the
repo-root proof path above for the accepted multimodal runtime authority.

```python
from zpe_multimodal import decode, encode

ids = encode("Hello ZPE")
text = decode(ids)
```

---

<p>
  <img src="../../.github/assets/readme/section-bars/public-api-contract.svg" alt="PUBLIC API CONTRACT" width="100%">
</p>

The stable text compatibility contract remains available for downstream
adapters and parity checks. It is not the primary public authority story.

- `zpe_multimodal.encode(text: str) -> list[int]`
- `zpe_multimodal.decode(ids: list[int] | tuple[int, ...]) -> str`
- `zpe_multimodal.ZPETokenizer`
  - `from_lattice(path: str) -> ZPETokenizer`
  - `encode(text: str) -> list[int]`
  - `decode(ids: list[int] | tuple[int, ...]) -> str`

---

<p>
  <img src="../../.github/assets/readme/section-bars/optional-dependency-groups.svg" alt="OPTIONAL DEPENDENCY GROUPS" width="100%">
</p>

- `diagram`: diagram helpers.
- `music`: MusicXML parser integrations.
- `voice-optional`: optional voice transcription/phoneme helpers.
- `voice-audio-heavy`: heavier optional audio stack.
- `hf`: HuggingFace integration path (`transformers` + `huggingface_hub`).
- `onnx`: ONNX export/runtime path.
- `wasm`: WASM runtime path.
- `triton`: Triton serving and streaming stack.
- `bench`: benchmarking and profiling tooling.
- `full`: existing broad optional set (`diagram`, `music`).
- `dev`: test/build tooling.

Example:

```bash
pip install -e ".[hf,onnx,bench]"
```

HuggingFace boundary notes:
- Core text compatibility APIs do not require `hf`.
- Adapter calls that touch Hub/pretrained integration require `.[hf]`.
- Torch is optional and only needed when requesting tensor outputs (`return_tensors='pt'`).
- If optional deps are missing, adapter code raises actionable runtime errors with install hints.

---

<p>
  <img src="../../.github/assets/readme/section-bars/cli.svg" alt="CLI" width="100%">
</p>

```bash
zpe-imc info --json
zpe-imc validate --stream-json "[1,2,3]" --json
zpe-imc demo --json
```

---

<p>
  <img src="../../.github/assets/readme/section-bars/compatibility-note-for-parallel-tracks.svg" alt="COMPATIBILITY NOTE FOR PARALLEL TRACKS" width="100%">
</p>

- A2 (HuggingFace) can depend on the stable text compatibility surface and
  the `hf` extra.
- A3 (adapters) can rely on the stable top-level text compatibility contract
  from this package.
- A5 (WASM) can target parity against `encode/decode` behavior.
- A6 (ONNX) can target parity against the class-based text compatibility API
  and the `onnx` extra.

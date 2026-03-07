# ZPE Triton Model Repository Template

This repository contains a serving scaffold for tokenizer-first inference.

Models:
- `zpe_tokenizer_onnx`: ONNX tokenizer model (output token IDs).
- `zpe_token_passthrough`: Python backend placeholder for downstream model replacement.
- `zpe_tokenizer_ensemble`: Ensemble that chains tokenizer output into the downstream model.

Expected layout:
- `zpe_tokenizer_onnx/config.pbtxt`
- `zpe_tokenizer_onnx/1/model.onnx`
- `zpe_tokenizer_onnx/1/model.integrity.json`
- `zpe_token_passthrough/config.pbtxt`
- `zpe_token_passthrough/1/model.py`
- `zpe_tokenizer_ensemble/config.pbtxt`

Public audit integrity for the shipped tokenizer model is anchored by:

- `zpe_tokenizer_onnx/1/model.integrity.json`

That manifest is the public-safe integrity root for the shipped ONNX file.
It avoids depending on the excluded `proofs/artifacts/**` warehouse.

Operator/private refresh path from A6 output:

```bash
cp proofs/artifacts/2026-02-24_program_maximal/A6/exported/zpe_tokenizer_op.onnx \
   code/deployment/triton/model_repository/zpe_tokenizer_onnx/1/model.onnx
```

If the operator refreshes the model from A6, they must also refresh the
committed integrity manifest for the shipped public model.

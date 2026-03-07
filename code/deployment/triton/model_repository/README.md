# ZPE Triton Model Repository Template

This repository contains a serving scaffold for tokenizer-first inference.

Models:
- `zpe_tokenizer_onnx`: ONNX tokenizer model (output token IDs).
- `zpe_token_passthrough`: Python backend placeholder for downstream model replacement.
- `zpe_tokenizer_ensemble`: Ensemble that chains tokenizer output into the downstream model.

Expected layout:
- `zpe_tokenizer_onnx/config.pbtxt`
- `zpe_tokenizer_onnx/1/model.onnx`
- `zpe_token_passthrough/config.pbtxt`
- `zpe_token_passthrough/1/model.py`
- `zpe_tokenizer_ensemble/config.pbtxt`

To refresh tokenizer model artifact from A6 output:

```bash
cp proofs/artifacts/2026-02-24_program_maximal/A6/exported/zpe_tokenizer_op.onnx \
   code/deployment/triton/model_repository/zpe_tokenizer_onnx/1/model.onnx
```

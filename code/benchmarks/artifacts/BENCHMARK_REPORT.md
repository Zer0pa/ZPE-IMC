# A4 Benchmark Report

- Run ID: `A4-BENCH-20260307T230025Z`
- Git commit: `e316ddd77805fc59040b9d6a687c1241fe40eabc`
- Timestamp (UTC): `2026-03-07T23:00:32Z`
- Protocol version: `WS3_BENCHMARK_PROTOCOL_2026-03-05`
- Scenario directory: `/Users/Zer0pa/ZPE-IMC-REPO/code/benchmarks/scenarios`
- Profile filter: `all`
- Scenario count: `11`

| Scenario | Profile | Throughput (tokens/s) | p50 (ms) | p95 (ms) | Peak Memory (MB) | Deterministic |
|---|---|---:|---:|---:|---:|---|
| emoji_heavy_faces_and_objects | baseline | 91601.8438 | 0.5091 | 0.6012 | 0.0095 | True |
| emoji_heavy_zwj_and_skin_tones | baseline | 139184.4497 | 0.5282 | 0.5964 | 0.0086 | True |
| long_text_repeated_paragraph | baseline | 660414.5879 | 1.1415 | 1.2802 | 0.0323 | True |
| long_text_story_block | baseline | 510158.8594 | 0.7578 | 0.851 | 0.0163 | True |
| multilingual_global_mix_a | baseline | 194124.1343 | 0.4921 | 0.5818 | 0.0073 | True |
| multilingual_global_mix_b | baseline | 138174.991 | 0.6075 | 0.7496 | 0.0088 | True |
| multimodal_full_stack_small_image | baseline | 207990.4426 | 43.4814 | 47.1098 | 1.1504 | True |
| multimodal_full_stack_practical_image_256 | medium | 301754.7934 | 122.1424 | 123.2996 | 3.9448 | True |
| multimodal_full_stack_practical_image_512 | heavy | 311275.9898 | 365.0939 | 435.5511 | 12.453 | True |
| short_text_hello_ascii | baseline | 37500.615 | 0.3913 | 0.492 | 0.0065 | True |
| short_text_punctuation_mix | baseline | 105761.1425 | 0.4228 | 0.4984 | 0.0068 | True |

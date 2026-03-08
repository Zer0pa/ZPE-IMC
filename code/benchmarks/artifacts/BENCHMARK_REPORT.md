# A4 Benchmark Report

- Run ID: `A4-BENCH-20260307T131414Z`
- Git commit: `e316ddd77805fc59040b9d6a687c1241fe40eabc`
- Timestamp (UTC): `2026-03-07T13:14:21Z`
- Protocol version: `WS3_BENCHMARK_PROTOCOL_2026-03-05`
- Scenario directory: `/Users/Zer0pa/ZPE-IMC-REPO/code/benchmarks/scenarios`
- Profile filter: `all`
- Scenario count: `11`

| Scenario | Profile | Throughput (tokens/s) | p50 (ms) | p95 (ms) | Peak Memory (MB) | Deterministic |
|---|---|---:|---:|---:|---:|---|
| emoji_heavy_faces_and_objects | baseline | 94455.4824 | 0.5056 | 0.523 | 0.0095 | True |
| emoji_heavy_zwj_and_skin_tones | baseline | 139510.1274 | 0.5369 | 0.5601 | 0.0086 | True |
| long_text_repeated_paragraph | baseline | 644591.4643 | 1.1808 | 1.2408 | 0.0323 | True |
| long_text_story_block | baseline | 473141.8342 | 0.8276 | 0.9092 | 0.0163 | True |
| multilingual_global_mix_a | baseline | 187550.2028 | 0.5168 | 0.5629 | 0.0073 | True |
| multilingual_global_mix_b | baseline | 140186.2346 | 0.6013 | 0.7325 | 0.0088 | True |
| multimodal_full_stack_small_image | baseline | 222541.5042 | 40.9779 | 42.2351 | 1.151 | True |
| multimodal_full_stack_practical_image_256 | medium | 315577.1287 | 116.8902 | 118.6547 | 3.9447 | True |
| multimodal_full_stack_practical_image_512 | heavy | 345652.7026 | 343.804 | 346.2357 | 12.4531 | True |
| short_text_hello_ascii | baseline | 39278.8313 | 0.377 | 0.3962 | 0.0065 | True |
| short_text_punctuation_mix | baseline | 111554.9558 | 0.4077 | 0.4296 | 0.0068 | True |
